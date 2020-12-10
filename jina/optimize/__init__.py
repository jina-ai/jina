import os
from itertools import tee
import json
from pathlib import Path
import shutil
from ruamel.yaml import YAML

from jina.flow import Flow
from jina.helper import colored
from jina.logging import default_logger as logger
from .parameters import IntegerParameter, load_optimization_parameters


class FlowRunner:
    def __init__(
        self,
        index_document_generator=None,
        query_document_generator=None,
        index_batch_size=None,
        query_batch_size=None,
        pod_dir=None,
        env_yaml=None,
        overwrite_workspace=False,
    ):

        self.index_document_generator = index_document_generator
        self.query_document_generator = query_document_generator
        self.index_batch_size = index_batch_size
        self.query_batch_size = query_batch_size
        self.pod_dir = Path(pod_dir)
        self.env_yaml = env_yaml
        self.overwrite_workspace = overwrite_workspace

    @staticmethod
    def clean_workdir(workspace):
        if workspace.exists():
            shutil.rmtree(workspace)
            logger.warning(colored("Existing workspace deleted", "red"))
            logger.warning(colored("WORKSPACE: " + str(workspace), "red"))

    def _create_trial_pods(self, trial_dir, trial_parameters):
        if self.pod_workspace.exists():
            shutil.rmtree(self.pod_workspace)
        shutil.copytree(self.pod_dir, self.pod_workspace)
        yaml = YAML(typ="rt")
        for file_path in self.pod_dir.glob("*.yml"):
            parameters = yaml.load(file_path)
            if "components" in parameters:
                for i, component in enumerate(parameters["components"]):
                    parameters["components"][i] = Optimizer._replace_param(
                        component, trial_parameters
                    )
            parameters = Optimizer._replace_param(parameters, trial_parameters)
            new_pod_file_path = self.pod_workspace / file_path.name
            yaml.dump(parameters, open(new_pod_file_path, "w"))

    def _create_trial_flow(self, flow_yaml, trial_dir):
        yaml = YAML(typ="rt")
        parameters = yaml.load(flow_yaml)
        for pod, val in parameters["pods"].items():
            for pod_param in parameters["pods"][pod].keys():
                if pod_param.startswith("uses"):
                    parameters["pods"][pod][pod_param] = str(
                        trial_dir / self.pod_dir / Path(val[pod_param]).name
                    )
        trial_flow_file_path = self.flow_workspace / flow_yaml.name
        yaml.dump(parameters, open(trial_flow_file_path, "w"))
        return trial_flow_file_path

    def _load_env(self):
        if self.env_yaml:
            yaml = YAML(typ="safe")
            self.env_parameters = yaml.load(open(self.env_yaml))
            for environment_variable, value in self.env_parameters.items():
                os.environ[environment_variable] = str(value)
            logger.info("Environment variables loaded")
        else:
            logger.info("Cannot load environment variables as no env_yaml passed")

    def _setup_workspace(self, workspace):
        workspace.mkdir(exist_ok=True)
        self.index_workspace = workspace / "index"
        self.index_workspace.mkdir(exist_ok=True)
        self.pod_workspace = workspace / "pods"
        self.flow_workspace = workspace / "flows"
        self.flow_workspace.mkdir(exist_ok=True)

    def run_indexing(self, index_yaml, trial_parameters, workspace="workspace"):
        self._load_env()
        if workspace.exists():
            if self.overwrite_workspace:
                FlowRunner.clean_workdir(workspace)
                logger.warning(
                    colored("change overwrite_workspace to change this", "red")
                )
            else:

                logger.warning(
                    colored(
                        "Workspace already exists. Skipping indexing.",
                        "cyan",
                    )
                )
                return

        self._setup_workspace(workspace)
        self._create_trial_pods(workspace, trial_parameters)
        index_yaml = self._create_trial_flow(index_yaml, workspace)

        self.index_document_generator, index_document_generator = tee(
            self.index_document_generator
        )

        with Flow.load_config(index_yaml) as f:
            f.index(index_document_generator, batch_size=self.index_batch_size)

    def run_querying(
        self, query_yaml, trial_parameters, callback, workspace="workspace"
    ):
        self._load_env()

        self._setup_workspace(workspace)
        self._create_trial_pods(workspace, trial_parameters)
        query_yaml = self._create_trial_flow(query_yaml, workspace)

        self.query_document_generator, query_document_generator = tee(
            self.query_document_generator
        )

        with Flow.load_config(query_yaml) as f:
            f.search(
                query_document_generator,
                batch_size=self.query_batch_size,
                output_fn=callback,
            )


class EvaluationCallback:
    def __init__(self, op_name=None):
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


class Optimizer:
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

    @staticmethod
    def _replace_param(parameters, trial_parameters):
        for section in ["with", "metas"]:
            if section in parameters:
                for param, val in parameters[section].items():
                    val = str(val).lstrip("$")
                    if val in trial_parameters:
                        parameters[section][param] = trial_parameters[val]
        return parameters

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