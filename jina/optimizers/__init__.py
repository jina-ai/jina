import os
from collections import defaultdict
from typing import Optional

import numpy as np
import yaml

from .parameters import (
    IntegerParameter,
    UniformParameter,
    LogUniformParameter,
    CategoricalParameter,
    DiscreteUniformParameter,
)
from .parameters import load_optimization_parameters
from ..helper import colored
from ..importer import ImportExtensions
from ..jaml import JAMLCompatible, JAML
from ..logging.predefined import default_logger as logger
from ..types.request import Response

if False:
    from .flow_runner import FlowRunner
    import optuna
    from optuna.trial import Trial
    from argparse import Namespace


class OptimizerCallback(JAMLCompatible):
    """
    Callback interface for storing and calculating evaluation metric during an optimization.
    Should be used, whenever a custom evaluation aggregation during an Flow optimization is needed.
    """

    def get_empty_copy(self) -> 'OptimizerCallback':
        """
        Return an empty copy of the :class:`OptimizerCallback`.

        .. # noqa: DAR202
        :raises NotImplementedError: :class:`OptimizerCallback` is just an interface. Please use any implemented subclass.
        """
        raise NotImplementedError

    def get_final_evaluation(self) -> float:
        """
        Return the aggregation of all evaluation collected via :method:`__call__`

        .. # noqa: DAR202
        :raises NotImplementedError: :class:`OptimizerCallback` is just an interface. Please use any implemented subclass.
        """
        raise NotImplementedError

    def __call__(self, response: 'Response'):
        """
        Collects the results of evaluators in the response object for aggregation.

        :param response: A response object of a Flow.
        :raises NotImplementedError: :class:`OptimizerCallback` is just an interface. Please use any implemented subclass.
        """
        raise NotImplementedError


class EvaluationCallback(OptimizerCallback):
    """
    Calculates an aggregation of all evaluations during a single :py:class:`FlowRunner`
    execution from the :py:class:`FlowOptimizer` with a given operator.

    Valid operators are: `['min', 'max', 'mean', 'median', 'sum', 'prod']`
    """

    AGGREGATE_FUNCTIONS = ['min', 'max', 'mean', 'median', 'sum', 'prod']

    def __init__(self, eval_name: Optional[str] = None, operation: str = 'mean'):
        """
        :param eval_name: evaluation name as required by the evaluator. Not needed if only 1 evaluator is used
        :param operation: name of the operation to be performed when getting the final evaluation
        """
        self._operation = operation
        if operation in self.AGGREGATE_FUNCTIONS:
            self.np_aggregate_function = getattr(np, operation)
        else:
            raise ValueError(
                f'The operation "{operation}" is not among the supported operators "{self.AGGREGATE_FUNCTIONS}".'
            )

        self._eval_name = eval_name
        self._evaluation_values = defaultdict(list)
        self._n_docs = 0

    def get_empty_copy(self):
        """
        Return an empty copy of the :class:`EvaluationCallback`.

        :return: Evaluation values
        """
        return EvaluationCallback(self._eval_name, self._operation)

    def get_final_evaluation(self):
        """
        Calculates and returns evaluation value on the metric defined in the :method:`__init__`.

        :return:: The aggregation of all evaluation collected via :method:`__call__`
        """
        if self._eval_name is not None:
            evaluation_name = self._eval_name
        else:
            evaluation_name = list(self._evaluation_values)[0]
            if len(self._evaluation_values) > 1:
                logger.warning(
                    f'More than one evaluation metric found. Please define the right eval_name. Currently {evaluation_name} is used'
                )

        return self.np_aggregate_function(self._evaluation_values[evaluation_name])

    def __call__(self, response: 'Response'):
        """
        Store the evaluation values

        :param response: response message
        """
        self._n_docs += len(response.data.docs)
        logger.info(f'Num of docs evaluated: {self._n_docs}')
        for doc in response.data.docs:
            for evaluation in doc.evaluations:
                self._evaluation_values[evaluation.op_name].append(evaluation.value)


class ResultProcessor(JAMLCompatible):
    """Result processor for the Optimizer."""

    def __init__(self, study: 'optuna.study.Study'):
        """
        :param study: optuna study object
        """
        self._study = study
        self._best_parameters = study.best_trial.params
        logger.info(colored(f'Number of finished trials: {len(study.trials)}', 'green'))
        logger.info(colored(f'Best trial: {study.best_trial.params}', 'green'))
        logger.info(colored(f'Time to finish: {study.best_trial.duration}', 'green'))

    @property
    def study(self):
        """
        :return:: Raw optuna study as calculated by the :py:class:`FlowOptimizer`.
        """
        return self._study

    @property
    def best_parameters(self):
        """
        :return:: The parameter set, which got the best evaluation result during the optimization.
        """
        return self._best_parameters

    def save_parameters(self, filepath: str = 'config/best_config.yml'):
        """
        Stores the best parameters in the given file.

        :param filepath: path where the best parameter config will be saved
        """
        parameter_dir = os.path.dirname(filepath)
        os.makedirs(parameter_dir, exist_ok=True)
        yaml.dump(self.best_parameters, open(filepath, 'w'))


class FlowOptimizer(JAMLCompatible):
    """
    Optimizer runs the given flows on multiple parameter configurations in order
    to find the best performing parameters. Uses `optuna` behind the scenes.
    For a detailed information how the parameters are sampled by optuna see
    https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html
    """

    def __init__(
        self,
        flow_runner: 'FlowRunner',
        parameter_yaml: str,
        evaluation_callback: 'OptimizerCallback',
        n_trials: int,
        workspace_base_dir: str = '.',
        sampler: str = 'TPESampler',
        direction: str = 'maximize',
        seed: int = 42,
    ):
        """
        :param flow_runner: `FlowRunner` object which contains the flows to be run.
        :param parameter_yaml: yaml container the parameters to be optimized
        :param evaluation_callback: The callback object, which stores the evaluation results
        :param n_trials: evaluation trials to be run
        :param workspace_base_dir: directory in which all temporary created data should be stored
        :param sampler: The optuna sampler. For a list of usable names see: https://optuna.readthedocs.io/en/stable/reference/samplers.html
        :param direction: direction of the optimization from either of `maximize` or `minimize`
        :param seed: random seed for reproducibility
        """
        super().__init__()
        self._version = '1'
        self._flow_runner = flow_runner
        self._parameter_yaml = parameter_yaml
        self._workspace_base_dir = workspace_base_dir
        self._evaluation_callback = evaluation_callback
        self._n_trials = n_trials
        self._sampler = sampler
        self._direction = direction
        self._seed = seed
        self.parameters = load_optimization_parameters(self._parameter_yaml)

    def _trial_parameter_sampler(self, trial: 'Trial'):
        trial_parameters = {}
        for param in self.parameters:
            param.update_trial_params(trial, trial_parameters)

        trial.workspace = (
            self._workspace_base_dir
            + '/JINA_WORKSPACE_'
            + '_'.join([str(v) for v in trial_parameters.values()])
        )

        trial_parameters['JINA_OPTIMIZER_TRIAL_WORKSPACE'] = trial.workspace

        return trial_parameters

    def _objective(self, trial: 'Trial'):
        trial_parameters = self._trial_parameter_sampler(trial)
        evaluation_callback = self._evaluation_callback.get_empty_copy()
        self._flow_runner.run(
            trial_parameters, workspace=trial.workspace, callback=evaluation_callback
        )
        eval_score = evaluation_callback.get_final_evaluation()
        logger.info(colored(f'Evaluation Score: {eval_score}', 'green'))
        return eval_score

    def optimize_flow(self, **kwargs) -> 'ResultProcessor':
        """
        Will run the actual optimization.

        :param kwargs: extra parameters for optuna sampler
        :return:: The aggregated result of the optimization run as a :class:`ResultProcessor`.
        """
        with ImportExtensions(required=True):
            import optuna
        if self._sampler == 'GridSampler':
            sampler = getattr(optuna.samplers, self._sampler)(**kwargs)
        else:
            sampler = getattr(optuna.samplers, self._sampler)(seed=self._seed, **kwargs)
        study = optuna.create_study(direction=self._direction, sampler=sampler)
        study.optimize(self._objective, n_trials=self._n_trials)
        result_processor = ResultProcessor(study)
        return result_processor


def run_optimizer_cli(args: 'Namespace'):
    """
    Used to run the FlowOptimizer from command line interface.

    :param args: arguments passed via cli
    """
    # The following import is needed to initialize the JAML parser
    from .flow_runner import SingleFlowRunner, MultiFlowRunner

    with open(args.uses) as f:
        optimizer = JAML.load(f)
    result_processor = optimizer.optimize_flow()
    if args.output_dir:
        result_processor.save_parameters(
            os.path.join(args.output_dir, 'best_parameters.yml')
        )
