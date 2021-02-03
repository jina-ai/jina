import os
import shutil
from collections.abc import Iterable
from typing import Iterable, Optional, Union, List

from ..flow import Flow
from ..helper import colored
from ..logging import default_logger as logger
from ..jaml import JAMLCompatible


class FlowRunner(JAMLCompatible):
    """An abstract FlowRunner object in Jina."""

    def run(
        self,
        trial_parameters: dict,
        workspace: str = 'workspace',
        callback=None,
        **kwargs,
    ):
        """Runs the defined flow(s).
        :param trial_parameters: parameters to be used as context
        :param workspace: directory to be used for the flows
        :param callback: callback that will be called by the flows. Should store the evaluation results.
        """
        raise NotImplementedError


class SingleFlowRunner(FlowRunner):
    """Module to define and run a flow.
       `documents` maps to a parameter of the `execution_method`, depending on the method.
       If you use a generator function/list as documents, the default will work out of the box.
       Otherwise, the following settings will work:

       indexing + jsonlines file: `execution_methos='index_lines', documents_parameter_name='filepath'`
       search + jsonlines file: `execution_methos='search_lines', documents_parameter_name='filepath'`

       indexing + file pattern: `execution_methos='index_files', documents_parameter_name='pattern'`
       search + file pattern: `execution_methos='search_files', documents_parameter_name='pattern'`

       For more reasonable values, have a look at the `Flow`.
    """

    def __init__(
        self,
        flow_yaml: str,
        documents: Union[Iterable, str],
        request_size: int,
        execution_method: str,
        documents_parameter_name: Optional[str] = 'input_fn',
        overwrite_workspace: bool = False,
    ):
        """
        :param flow_yaml: path to Flow yaml
        :param documents: input parameter for `execution_method` for iterating documents.
        (e.g. a list of documents for `index` or a .jsonlines file for `index_lines`)
        :param request_size: request size used in the flow
        :param execution_method: one of the methods of the Jina :py:class:`Flow` (e.g. `index_lines`)
        :param documents_parameter_name: to which parameter of the `execution_function` the `documents` will be mapped.
        See `jina/flow/__init__.py::Flow` for more details.
        :param overwrite_workspace: True, means workspace created by the Flow will be overwriten
        """
        super().__init__()
        self._flow_yaml = flow_yaml

        if type(documents) is str:
            self._documents = documents

        elif isinstance(documents, Iterable):
            self._documents = list(documents)
        else:
            raise TypeError(f"documents is of wrong type: {type(documents)}")

        self._request_size = request_size
        self._execution_method = execution_method
        self._documents_parameter_name = documents_parameter_name
        self._overwrite_workspace = overwrite_workspace

    def _setup_workspace(self, workspace):
        if os.path.exists(workspace):
            if self._overwrite_workspace:
                shutil.rmtree(workspace)
                logger.warning(colored('Existing workspace deleted', 'red'))
                logger.warning(colored('WORKSPACE: ' + str(workspace), 'red'))
                logger.warning(
                    colored('change overwrite_workspace to change this', 'red')
                )
            else:
                logger.warning(
                    colored(
                        f'Workspace {workspace} already exists. Please set ``overwrite_workspace=True`` for replacing it.',
                        'red',
                    )
                )

        os.makedirs(workspace, exist_ok=True)

    def run(
        self,
        trial_parameters: dict,
        workspace: str = 'workspace',
        callback=None,
        **kwargs,
    ):
        """Runs a Flow according to the definition of the `FlowRunner`.

        :param trial_parameters: context for the Flow
        :param workspace: directory to be used for artifacts generated
        :param callback: The callback function, which should store results comming from evaluation.
        """

        self._setup_workspace(workspace)
        additional_arguments = {self._documents_parameter_name: self._documents}
        additional_arguments.update(kwargs)
        with Flow.load_config(self._flow_yaml, context=trial_parameters) as f:
            getattr(f, self._execution_method)(
                request_size=self._request_size,
                on_done=callback,
                **additional_arguments,
            )


class MultiFlowRunner(FlowRunner):
    """Chain and run multiple Flows. It is an interface for common patterns like IndexFlow -> SearchFlow"""

    def __init__(self, flows: List[FlowRunner]):
        """
        :param flows: Flows to be executed in sequence
        """
        super().__init__()
        self.flows = flows

    def run(
        self,
        trial_parameters: dict,
        workspace: str = 'workspace',
        callback=None,
        **kwargs,
    ):
        """
        :param trial_parameters: parameters to be used as environment variables
        :param workspace: directory to be used for the flows
        :param callback: will be forwarded to every single Flow.
        """
        for flow in self.flows:
            flow.run(trial_parameters, workspace, callback, **kwargs)
