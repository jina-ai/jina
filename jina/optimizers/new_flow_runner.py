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
        flow_yaml,
        document_generator,
        batch_size,
        pod_dir,
        task,  # this can be only index or search as it is used to call the flow API
        callback=None,
        env_yaml=None,
        overwrite_workspace=False,
    ):
        self.flow_yaml = flow_yaml
        self.document_generator = document_generator
        self.batch_size = batch_size
        self.pod_dir = Path(pod_dir)
        self.task = task
        self.callback = callback
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

    def _add_env_parameters(self, trial_parameters):
        if self.env_yaml:
            yaml = YAML(typ="safe")
            env_parameters = yaml.load(open(self.env_yaml))
            for environment_variable, value in env_parameters.items():
                trial_parameters[environment_variable] = str(value)
            logger.info("Environment variables loaded")
        else:
            logger.info("Cannot load environment variables as no env_yaml passed")
        return trial_parameters

    def _setup_workspace(self, workspace):
        workspace.mkdir(exist_ok=True)
        self.index_workspace = workspace / "index"
        self.index_workspace.mkdir(exist_ok=True)
        self.pod_workspace = workspace / "pods"
        self.flow_workspace = workspace / "flows"
        self.flow_workspace.mkdir(exist_ok=True)

    def run(self, trial_parameters=None, workspace="workspace"):
        if trial_parameters is None:
            trial_parameters = {}

        trial_parameters = self._add_env_parameters(trial_parameters)

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
        flow_yaml = self._create_trial_flow(self.flow_yaml, workspace)

        self.document_generator, document_generator = tee(self.document_generator)

        with Flow.load_config(flow_yaml) as f:
            getattr(f, self.task)(
                document_generator, batch_size=self.batch_size, output_fn=self.callback
            )


# Example of how to use it

index_flow = FlowRunner(
    flow_yaml="flows/index.yml",
    document_generator=doc_gen,
    batch_size=64,
    pod_dir="pods",
    callback=None,
    task="index",
    overwrite_workspace=True,
)

query_flow = FlowRunner(
    flow_yaml="flows/query.yml",
    document_generator=doc_gen,
    batch_size=64,
    pod_dir="pods",
    callback=callback,
    task="search",
)


class MultiFlowRunner:
    def __init__(self, flows, workspace="workspace"):
        self.flows = flows
        self.workspace = workspace

    def run(self, trial_parameters):
        for flow in self.flows:
            flow.run(trial_parameters, self.workspace)


my_runner = MultiFlowRunner([index_flow, query_flow], workspace="trial")
trial_parameters = {"JINA_MYENCODER_TARGET_DIMENSION": 32}
my_runner.run(trial_parameters)
