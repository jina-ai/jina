from collections import defaultdict
import os
from typing import Optional

import yaml

from ..helper import colored
from ..importer import ImportExtensions
from ..logging import default_logger as logger
from .parameters import load_optimization_parameters
from ..jaml import JAML, JAMLCompatible

if False:
    from .flow_runner import FlowRunner
    import optuna


class EvaluationCallback:
    """Callback for storing and calculating evaluation metric."""

    def __init__(self, eval_name: Optional[str] = None):
        """
        :param eval_name: evaluation name as required by evaluator. Not needed if only 1 evaluator is used
        """
        self.eval_name = eval_name
        self.evaluation_values = defaultdict(float)
        self.n_docs = 0

    def get_fresh_callback(self):
        """Creates a new callback"""
        return EvaluationCallback(self.eval_name)

    def get_mean_evaluation(self):
        """Returns mean evaluation value on the eval_name."""
        if self.eval_name:
            evaluation = {self.eval_name: self.evaluation_values[self.eval_name] / self.n_docs}
        else:
            evaluation = {metric: val / self.n_docs for metric, val in self.evaluation_values.items()}

        if (len(evaluation.keys()) > 1) and (self.eval_name is None):
            logger.warning(f'More than one evaluation metric found. Please use the right eval_name. Currently {list(evaluation)[0]} is used')

        return evaluation

    def __call__(self, response):
        self.n_docs += len(response.search.docs)
        logger.info(f'Num of docs evaluated: {self.n_docs}')
        for doc in response.search.docs:
            for evaluation in doc.evaluations:
                self.evaluation_values[evaluation.op_name] = (
                    self.evaluation_values.get(evaluation.op_name, 0.0)
                    + evaluation.value
                )


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
        workspace_base_dir: str = '',
        workspace_env: str = 'JINA_WORKSPACE',
    ):
        """
        :param flow_runner: `FlowRunner` object which contains the flows to be run.
        :param parameter_yaml: yaml container the parameters to be optimized
        :param workspace_env: workspace env name as referred in pods and flows yaml
        """
        super().__init__()
        self._version = '1'
        self.flow_runner = flow_runner
        self.parameter_yaml = parameter_yaml
        self.workspace_env = workspace_env.lstrip('$')
        self.workspace_base_dir = workspace_base_dir

    @property
    def yaml_spec(self):
        return JAML.dump(self)

    def _trial_parameter_sampler(self, trial):
        trial_parameters = {}
        parameters = load_optimization_parameters(self.parameter_yaml)
        for param in parameters:
            trial_parameters[param.env_var] = getattr(trial, param.optuna_method)(
                **param.to_optuna_args()
            )

        trial_workspace = self.workspace_base_dir + '/JINA_WORKSPACE_' + '_'.join([str(v) for v in trial_parameters.values()])

        trial_parameters[self.workspace_env] = trial_workspace
        trial.workspace = trial_workspace
        return trial_parameters

    def _objective(self, trial):
        trial_parameters = self._trial_parameter_sampler(trial)
        self.flow_runner.run(trial_parameters, workspace=trial.workspace)
        evaluation = self.flow_runner.get_evaluations()
        op_name = list(evaluation)[0]
        eval_score = evaluation[op_name]
        logger.info(colored(f'Avg {op_name}: {eval_score}', 'green'))
        return eval_score

    def optimize_flow(
        self,
        n_trials: int,
        sampler: str = 'TPESampler',
        direction: str = 'maximize',
        seed: int = 42,
        result_processor: 'OptunaResultProcessor' = OptunaResultProcessor,
        **kwargs
    ):
        """
        :param n_trials: evaluation trials to be run
        :param sampler: optuna sampler
        :param direction: direction of the optimization from either of `maximize` or `minimize`
        :param seed: random seed for reproducibility
        :param kwargs: extra parameters for optuna sampler
        """
        with ImportExtensions(required=True):
            import optuna
        if sampler == 'GridSampler':
            sampler = getattr(optuna.samplers, sampler)(**kwargs)
        else:
            sampler = getattr(optuna.samplers, sampler)(seed=seed, **kwargs)
        study = optuna.create_study(direction=direction, sampler=sampler)
        study.optimize(self._objective, n_trials=n_trials)
        return result_processor(study)
