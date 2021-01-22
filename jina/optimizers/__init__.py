from collections import defaultdict
import os
from typing import Optional

import yaml

from ..helper import colored
from ..importer import ImportExtensions
from ..logging import default_logger as logger
from .parameters import load_optimization_parameters
from ..jaml import JAMLCompatible

if False:
    from .flow_runner import FlowRunner
    import optuna


class OptimizerCallback(JAMLCompatible):

    def get_empty_cops(self) -> 'OptimizerCallback':
        raise NotImplementedError

    def get_final_evaluation(self) -> float:
        raise NotImplementedError

    def __call__(self, response):
        raise NotImplementedError


class MeanEvaluationCallback(OptimizerCallback):
    """Callback for storing and calculating evaluation metric."""

    def __init__(self, eval_name: Optional[str] = None):
        """
        :param eval_name: evaluation name as required by evaluator. Not needed if only 1 evaluator is used
        """
        self.eval_name = eval_name
        self.evaluation_values = defaultdict(float)
        self.n_docs = 0

    def get_empty_copy(self):
        return MeanEvaluationCallback(self.eval_name)

    def get_final_evaluation(self):
        """Returns mean evaluation value on the eval_name."""
        if self.eval_name is not None:
            evaluation_name = self.eval_name
        else:
            evaluation_name = list(self.evaluation_values)[0]
            if len(self.evaluation_values) > 1:
                logger.warning(f'More than one evaluation metric found. Please define the right eval_name. Currently {evaluation_name} is used')

        return self.evaluation_values[evaluation_name] / self.n_docs

    def __call__(self, response):
        self.n_docs += len(response.search.docs)
        logger.info(f'Num of docs evaluated: {self.n_docs}')
        for doc in response.search.docs:
            for evaluation in doc.evaluations:
                self.evaluation_values[evaluation.op_name] += evaluation.value


class OptunaResultProcessor:
    """Result processor for Optuna"""

    def __init__(self, study: 'optuna.study.Study'):
        """
        :param study: optuna study object
        """
        self.study = study
        self.best_parameters = study.best_trial.params
        logger.info(colored(f'Number of finished trials: {len(study.trials)}', 'green'))
        logger.info(colored(f'Best trial: {study.best_trial.params}', 'green'))
        logger.info(colored(f'Time to finish: {study.best_trial.duration}', 'green'))

    def save_parameters(self, filepath: str = 'config/best_config.yml'):
        """
        :param filepath: path where the best parameter config will be saved
        """
        parameter_dir = os.path.dirname(filepath)
        os.makedirs(parameter_dir, exist_ok=True)
        yaml.dump(self.best_parameters, open(filepath, 'w'))


class OptunaOptimizer(JAMLCompatible):
    """Optimizer which uses Optuna to run flows and choose best parameters."""

    def __init__(
        self,
        flow_runner: 'FlowRunner',
        parameter_yaml: str,
        evaluation_callback: 'OptimizerCallback',
        n_trials: int,
        workspace_base_dir: str = '',
        sampler: str = 'TPESampler',
        direction: str = 'maximize',
        seed: int = 42,

    ):
        """
        :param flow_runner: `FlowRunner` object which contains the flows to be run.
        :param parameter_yaml: yaml container the parameters to be optimized
        :param n_trials: evaluation trials to be run
        :param sampler: optuna sampler
        :param direction: direction of the optimization from either of `maximize` or `minimize`
        :param seed: random seed for reproducibility
        """
        super().__init__()
        self._version = '1'
        self.flow_runner = flow_runner
        self.parameter_yaml = parameter_yaml
        self.workspace_base_dir = workspace_base_dir
        self.evaluation_callback = evaluation_callback
        self.n_trials = n_trials
        self.sampler = sampler
        self.direction = direction
        self.seed = seed

    def _trial_parameter_sampler(self, trial):
        trial_parameters = {}
        parameters = load_optimization_parameters(self.parameter_yaml)
        for param in parameters:
            trial_parameters[param.jaml_variable] = getattr(trial, param.optuna_method)(
                **param.to_optuna_args()
            )

        trial.workspace = self.workspace_base_dir + '/JINA_WORKSPACE_' + '_'.join([str(v) for v in trial_parameters.values()])

        return trial_parameters

    def _objective(self, trial):
        trial_parameters = self._trial_parameter_sampler(trial)
        evaluation_callback = self.evaluation_callback.get_empty_copy()
        self.flow_runner.run(trial_parameters, workspace=trial.workspace, callback=evaluation_callback)
        eval_score = evaluation_callback.get_final_evaluation()
        logger.info(colored(f'Evaluation Score: {eval_score}', 'green'))
        return eval_score

    def optimize_flow(
        self,
        result_processor: 'OptunaResultProcessor' = OptunaResultProcessor,
        **kwargs
    ):
        """
        :param kwargs: extra parameters for optuna sampler
        """
        with ImportExtensions(required=True):
            import optuna
        if self.sampler == 'GridSampler':
            sampler = getattr(optuna.samplers, self.sampler)(**kwargs)
        else:
            sampler = getattr(optuna.samplers, self.sampler)(seed=self.seed, **kwargs)
        study = optuna.create_study(direction=self.direction, sampler=sampler)
        study.optimize(self._objective, n_trials=self.n_trials)
        return result_processor(study)


# def run_yaml_optimizer(yaml_file):
#     optimizer = JAML.load(optimizer_yaml)
#     result = optimizer.optimize_flow(n_trials=10)

#     result_path = str(tmpdir) + '/results/best_parameters.yml'
#     result.save_parameters(result_path)
#     parameters = result.best_parameters

