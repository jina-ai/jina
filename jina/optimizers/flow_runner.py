import os
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
        documents,
        batch_size,
        pod_dir,
        task,  # this can be only index or search as it is used to call the flow API
        callback=None,
        overwrite_workspace=False,
    ):
        self.flow_yaml = Path(flow_yaml)
        # Todo: Make changes for working with doc generator
        self.documents = documents if type(documents) == list else list(documents)
        self.batch_size = batch_size
        self.pod_dir = Path(pod_dir)
        self.task = task
        self.callback = callback
        self.overwrite_workspace = overwrite_workspace

    @staticmethod
    def clean_workdir(workspace):
        if workspace.exists():
            shutil.rmtree(workspace)
            logger.warning(colored("Existing workspace deleted", "red"))
            logger.warning(colored("WORKSPACE: " + str(workspace), "red"))

    def _create_trial_flow(self, trial_dir, trial_parameters):
        flow_workspace = trial_dir / "flows"
        flow_workspace.mkdir(exist_ok=True)

        yaml = YAML(typ="rt")
        parameters = yaml.load(self.flow_yaml)
        for env in parameters["env"].keys():
            if env in trial_parameters:
                parameters["env"][env] = trial_parameters[env]
        trial_flow_file_path = flow_workspace / self.flow_yaml.name
        yaml.dump(parameters, open(trial_flow_file_path, "w"))
        return trial_flow_file_path

    def run(self, trial_parameters=None, workspace="workspace"):
        if trial_parameters is None:
            trial_parameters = {}

        if workspace.exists():
            if self.overwrite_workspace:
                FlowRunner.clean_workdir(workspace)
                logger.warning(
                    colored("change overwrite_workspace to change this", "red")
                )
            else:
                if self.task == "index":
                    logger.warning(
                        colored(
                            "Workspace already exists. Skipping indexing.",
                            "cyan",
                        )
                    )
                    return

        workspace.mkdir(exist_ok=True)
        flow_yaml = self._create_trial_flow(workspace, trial_parameters)
        with Flow.load_config(flow_yaml) as f:
            getattr(f, self.task)(
                self.documents,
                batch_size=self.batch_size,
                output_fn=self.callback,
            )


class MultiFlowRunner:
    def __init__(self, flows, workspace="workspace"):
        self.flows = flows
        self.workspace = workspace

    def run(self, trial_parameters):
        for flow in self.flows:
            flow.run(trial_parameters, self.workspace)
