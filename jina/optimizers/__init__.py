from pathlib import Path

from typing import Optional
from collections import defaultdict

from ..helper import colored
from ..jaml import JAML
from ..logging import default_logger as logger
from .parameters import load_optimization_parameters


if False:
    from .flow_runner import MultiFlowRunner


class EvaluationCallback:
    """Callback for storing and calculating evaluation metric."""

    def __init__(self, eval_name: Optional[str] = None):
        """
        :param eval_name: evaluation name as required by evaluator
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
            return self.evaluation_values[self.eval_name] / self.n_docs
        return {
            metric: val / self.n_docs for metric, val in self.evaluation_values.items()
        }

    def __call__(self, response):
        self.n_docs += len(response.search.docs)
        logger.info(f'Num of docs evaluated: {self.n_docs}')
        for doc in response.search.docs:
            for evaluation in doc.evaluations:
                self.evaluation_values[evaluation.op_name] = (
                    self.evaluation_values.get(evaluation.op_name, 0.0)
                    + evaluation.value
                )


class OptimizationResults:
    def __init__(self, params: dict):
        self.params = params

    def _dump_results(self, filepath: Path):
        filepath.parent.mkdir(exist_ok=True)
        JAML.dump(self.params, open(filepath, 'w'))


class OptunaOptimizer:
    """Optimizer which uses Optuna to run flows and choose best parameters."""

    def __init__(
        self,
        multi_flow: 'MultiFlowRunner',
        parameter_yaml: str,
        best_config_filepath: str = 'config/best_config.yml',
        workspace_env: str = 'JINA_WORKSPACE',
        eval_flow_index: int = -1,
    ):
        """
        :param multi_flow: `MultiFlowRunner` object which contains the flows to be run.
        :param parameter_yaml: yaml container the parameters to be optimized
        :param best_config_filepath: path where the best parameter config will be saved
        :param workspace_env: workspace env name as referred in pods and flows yaml
        :param eval_flow_index: index of the evaluation flow in the sequence of flows in `MultiFlowRunner`
        """
        self.multi_flow = multi_flow
        self.parameter_yaml = parameter_yaml
        self.best_config_filepath = Path(best_config_filepath)
        self.workspace_env = workspace_env.lstrip('$')
        self.eval_flow_index = eval_flow_index

    def _trial_parameter_sampler(self, trial):
        trial_parameters = {}
        parameters = load_optimization_parameters(self.parameter_yaml)
        for param in parameters:
            trial_parameters[param.env_var] = getattr(trial, param.method)(
                **param.to_optuna_args()
            )

        trial_workspace = Path(
            'JINA_WORKSPACE_' + '_'.join([str(v) for v in trial_parameters.values()])
        )
        trial_parameters[self.workspace_env] = str(trial_workspace)

        trial.workspace = trial_workspace
        return trial_parameters

    def _objective(self, trial):
        self.multi_flow.flows[self.eval_flow_index].callback = self.multi_flow.flows[
            self.eval_flow_index
        ].callback.get_fresh_callback()
        trial_parameters = self._trial_parameter_sampler(trial)
        self.multi_flow.run(trial_parameters, workspace=trial.workspace)
        evaluation_values = self.multi_flow.flows[
            self.eval_flow_index
        ].callback.get_mean_evaluation()
        op_name = list(evaluation_values)[0]
        mean_eval = evaluation_values[op_name]
        logger.info(colored(f'Avg {op_name}: {mean_eval}', 'green'))
        return mean_eval

    def _export_params(self, study):
        self.best_config_filepath.parent.mkdir(exist_ok=True)
        JAML.dump(study.best_trial.params, open(self.best_config_filepath, 'w'))

    def optimize_flow(
        self,
        n_trials: int,
        sampler: str = 'TPESampler',
        direction: str = 'maximize',
        seed: int = 42,
    ):
        """
        :param n_trials: evaluation trials to be run
        :param sampler: optuna sampler
        :param direction: direction of the optimization from either of `maximize` or `minimize`
        :param seed: random seed for reproducibility
        """
        import optuna

        sampler = getattr(optuna.samplers, sampler)(seed=seed)
        study = optuna.create_study(direction=direction, sampler=sampler)
        study.optimize(self._objective, n_trials=n_trials)
        logger.info(colored(f'Number of finished trials: {len(study.trials)}', 'green'))
        logger.info(colored(f'Best trial: {study.best_trial.params}', 'green'))
        logger.info(colored(f'Time to finish: {study.best_trial.duration}', 'green'))
        return OptimizationResults(study.best_trial.params)
