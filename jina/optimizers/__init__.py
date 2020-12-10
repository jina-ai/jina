from pathlib import Path
from ruamel.yaml import YAML

from jina.helper import colored
from jina.logging import default_logger as logger
from .parameters import load_optimization_parameters


class EvaluationCallback:
    def __init__(self, op_name=None):  # Todo: better name than op_name
        self.op_name = op_name
        self.evaluation_values = {}
        self.n_docs = 0

    def get_mean_evaluation(self):
        if self.op_name:
            return self.evaluation_values[self.op_name] / self.n_docs
        return {
            metric: val / self.n_docs for metric, val in self.evaluation_values.items()
        }

    def process_result(self, response):
        self.n_docs += len(response.search.docs)
        logger.info(f"Num of docs evaluated: {self.n_docs}")
        for doc in response.search.docs:
            for evaluation in doc.evaluations:
                self.evaluation_values[evaluation.op_name] = (
                    self.evaluation_values.get(evaluation.op_name, 0.0)
                    + evaluation.value
                )


class OptunaOptimizer:
    def __init__(
        self,
        flow_runner,
        index_yaml,
        query_yaml,
        parameter_yaml,
        callback=EvaluationCallback(),
        best_config_filepath="config/best_config.yml",
        workspace_env="JINA_WORKSPACE",
    ):
        self.flow_runner = flow_runner
        self.index_yaml = Path(index_yaml)
        self.query_yaml = Path(query_yaml)
        self.parameter_yaml = parameter_yaml
        self.callback = callback
        self.best_config_filepath = Path(best_config_filepath)
        self.workspace_env = workspace_env.lstrip("$")

    def _trial_parameter_sampler(self, trial):
        """https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial"""
        trial_parameters = {}
        parameters = load_optimization_parameters(self.parameter_yaml)
        for param in parameters:
            trial_parameters[param.env_var] = getattr(trial, param.method)(
                **param.to_optuna_args()
            )

        trial_workspace = Path(
            "JINA_WORKSPACE_" + "_".join([str(v) for v in trial_parameters.values()])
        )
        trial_parameters[self.workspace_env] = str(trial_workspace)

        trial.workspace = trial_workspace
        return trial_parameters

    def _objective(self, trial):
        trial_parameters = self._trial_parameter_sampler(trial)

        self.flow_runner.run_indexing(
            self.index_yaml, trial_parameters, trial.workspace
        )
        self.flow_runner.run_querying(
            self.query_yaml,
            trial_parameters,
            self.callback.process_result,
            trial.workspace,
        )

        evaluation_values = self.callback.get_mean_evaluation()
        op_name = list(evaluation_values)[0]
        mean_eval = evaluation_values[op_name]
        logger.info(colored(f"Avg {op_name}: {mean_eval}", "green"))
        return mean_eval

    def _export_params(self, study):
        self.best_config_filepath.parent.mkdir(exist_ok=True)
        yaml = YAML(typ="rt")
        all_params = {**self.flow_runner.env_parameters, **study.best_trial.params}
        yaml.dump(all_params, open(self.best_config_filepath, "w"))
        logger.info(colored(f"Number of finished trials: {len(study.trials)}", "green"))
        logger.info(colored(f"Best trial: {study.best_trial.params}", "green"))
        logger.info(colored(f"Time to finish: {study.best_trial.duration}", "green"))

    def optimize_flow(
        self, n_trials, sampler="TPESampler", direction="maximize", seed=42
    ):
        import optuna

        sampler = getattr(optuna.samplers, sampler)(seed=seed)
        study = optuna.create_study(direction=direction, sampler=sampler)
        study.optimize(self._objective, n_trials=n_trials)
        self._export_params(study)