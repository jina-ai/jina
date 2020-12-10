import os
from itertools import tee
from pathlib import Path
import shutil
from ruamel.yaml import YAML

from jina.flow import Flow
from jina.helper import colored
from jina.logging import default_logger as logger


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

    @staticmethod
    def _replace_param(parameters, trial_parameters):
        for section in ["with", "metas"]:
            if section in parameters:
                for param, val in parameters[section].items():
                    val = str(val).lstrip("$")
                    if val in trial_parameters:
                        parameters[section][param] = trial_parameters[val]
        return parameters

    def _create_trial_pods(self, trial_dir, trial_parameters):
        if self.pod_workspace.exists():
            shutil.rmtree(self.pod_workspace)
        shutil.copytree(self.pod_dir, self.pod_workspace)
        yaml = YAML(typ="rt")
        for file_path in self.pod_dir.glob("*.yml"):
            parameters = yaml.load(file_path)
            if "components" in parameters:
                for i, component in enumerate(parameters["components"]):
                    parameters["components"][i] = self._replace_param(
                        component, trial_parameters
                    )
            parameters = self._replace_param(parameters, trial_parameters)
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