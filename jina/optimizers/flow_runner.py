import os
import shutil
from typing import Iterator, Optional

from ..flow import Flow
from ..helper import colored
from ..logging import default_logger as logger


class FlowRunner:
    """Module to define and run a flow."""

    def __init__(
        self,
        flow_yaml: str,
        documents: Iterator,
        batch_size: int,
        task: str,  # this can be only index or search as it is used to call the flow API
        callback: Optional = None,
        overwrite_workspace: bool = False,
    ):
        """
        :param flow_yaml: path to flow yaml
        :param documents: iterator with list or generator for getting the documents
        :param batch_size: batch size used in the flow
        :param task: task of the flow which can be `index` or `search`
        :param callback: callback to be passed to the flow's `on_done`
        :param overwrite_workspace: overwrite workspace created by the flow
        """
        self.flow_yaml = flow_yaml
        # TODO: Make changes for working with doc generator (Pratik, before v1.0)
        self.documents = documents if type(documents) == list else list(documents)
        self.batch_size = batch_size
        if task in ('index', 'search'):
            self.task = task
        else:
            raise ValueError('task can be either of index or search')
        self.callback = callback
        self.overwrite_workspace = overwrite_workspace

    @staticmethod
    def clean_workdir(workspace):
        if workspace.exists():
            shutil.rmtree(workspace)
            logger.warning(colored('Existing workspace deleted', 'red'))
            logger.warning(colored('WORKSPACE: ' + str(workspace), 'red'))

    def _create_trial_flow(self, trial_dir, trial_parameters):
        import yaml

        class _Flow(yaml.YAMLObject):
            yaml_tag = u'!Flow'

        yaml.SafeLoader.add_constructor('!Flow', _Flow.from_yaml)
        yaml.SafeDumper.add_multi_representer(_Flow, _Flow.to_yaml)

        flow_workspace = trial_dir + '/flows'
        os.makedirs(flow_workspace, exist_ok=True)

        with open(self.flow_yaml) as f:
            parameters = yaml.load(f, Loader=yaml.Loader)
        if hasattr(parameters, 'env'):
            for env in parameters.env.keys():
                if env in trial_parameters:
                    parameters.env[env] = trial_parameters[env]
        trial_flow_file_path = flow_workspace + '/' + os.path.basename(self.flow_yaml)
        yaml.dump(parameters, open(trial_flow_file_path, 'w'))
        return trial_flow_file_path

    def run(self, trial_parameters=None, workspace='workspace', **kwargs):
        """[summary]

        :param trial_parameters: flow env variable values
        :param workspace: directory to be used for artifacts generated
        """

        if trial_parameters is None:
            trial_parameters = {}

        if os.path.exists(workspace):
            if self.overwrite_workspace:
                FlowRunner.clean_workdir(workspace)
                logger.warning(
                    colored('change overwrite_workspace to change this', 'red')
                )
            else:
                if self.task == 'index':
                    logger.warning(
                        colored(
                            'Workspace already exists. Skipping indexing.',
                            'cyan',
                        )
                    )
                    return

        os.makedirs(workspace, exist_ok=True)
        flow_yaml = str(self._create_trial_flow(workspace, trial_parameters))
        with Flow.load_config(flow_yaml) as f:
            getattr(f, self.task)(
                self.documents,
                batch_size=self.batch_size,
                on_done=self.callback,
                **kwargs
            )


class MultiFlowRunner:
    """Chain and run multiple flows"""

    def __init__(self, *flows):
        """
        :param flows: flows to be executed in sequence
        """
        self.flows = flows

    def run(
        self, trial_parameters: Optional[dict] = None, workspace: str = 'workspace'
    ):
        """
        :param trial_parameters: parameters to be used as environment variables
        :param workspace: directory to be used for the flows
        """
        for flow in self.flows:
            flow.run(trial_parameters, workspace)
