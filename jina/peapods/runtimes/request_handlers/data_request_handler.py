import re
from typing import Dict, List

from .... import __default_endpoint__
from ....excepts import (
    ExecutorFailToLoad,
    BadConfigSource,
)
from ....executors import BaseExecutor
from ....helper import typename
from ....types.arrays.document import DocumentArray


class DataRequestHandler:
    def __init__(self, args, logger, **kwargs):
        super().__init__()
        self.args = args
        self.logger = logger
        self._load_plugins()
        self._load_executor()

    def _load_plugins(self):
        """Load the plugins if needed necessary to load executors."""
        if self.args.py_modules:
            from ....importer import PathImporter

            PathImporter.add_modules(*self.args.py_modules)

    def _load_executor(self):
        """Load the executor to this runtime, specified by ``uses`` CLI argument."""
        try:
            self._executor = BaseExecutor.load_config(
                self.args.uses,
                override_with=self.args.uses_with,
                override_metas=self.args.uses_metas,
                override_requests=self.args.uses_requests,
                runtime_args=vars(self.args),
            )
        except BadConfigSource as ex:
            self.logger.error(
                f'fail to load config from {self.args.uses}, if you are using docker image for --uses, '
                f'please use "docker://YOUR_IMAGE_NAME"'
            )
            raise ExecutorFailToLoad from ex
        except FileNotFoundError as ex:
            self.logger.error(f'fail to load file dependency')
            raise ExecutorFailToLoad from ex
        except Exception as ex:
            self.logger.critical(f'can not load the executor from {self.args.uses}')
            raise ExecutorFailToLoad from ex

    @staticmethod
    def _parse_params(parameters: Dict, executor_name: str):
        parsed_params = parameters
        specific_parameters = parameters.get(executor_name, None)
        if specific_parameters:
            parsed_params.update(**specific_parameters)
        return parsed_params

    def handle(
        self,
        request,
        docs,
        docs_matrix,
        groundtruths,
        groundtruths_matrix,
        envelope,
        peapod_name,
    ):
        # skip executor if target_peapod mismatch
        if not re.match(envelope.header.target_peapod, peapod_name):
            self.logger.debug(
                f'skip executor: mismatch target, target: {envelope.header.target_peapod}, name: {peapod_name}'
            )
            return

        # skip executor if endpoints mismatch
        if (
            envelope.header.exec_endpoint not in self._executor.requests
            and __default_endpoint__ not in self._executor.requests
        ):
            self.logger.debug(
                f'skip executor: mismatch request, exec_endpoint: {envelope.header.exec_endpoint}, requests: {self._executor.requests}'
            )
            return

        params = self._parse_params(request.parameters, self._executor.metas.name)

        # executor logic
        r_docs = self._executor(
            req_endpoint=envelope.header.exec_endpoint,
            docs=docs,
            parameters=params,
            docs_matrix=docs_matrix,
            groundtruths=groundtruths,
            groundtruths_matrix=groundtruths_matrix,
        )

        # assigning result back to request
        # 1. Return none: do nothing
        # 2. Return nonempty and non-DocumentArray: raise error
        # 3. Return DocArray, but the memory pointer says it is the same as self.docs: do nothing
        # 4. Return DocArray and its not a shallow copy of self.docs: assign self.request.docs
        if r_docs is not None:
            if not isinstance(r_docs, DocumentArray):
                raise TypeError(
                    f'return type must be {DocumentArray!r} or None, but getting {typename(r_docs)}'
                )
            elif r_docs != request.docs:
                # this means the returned DocArray is a completely new one
                request.docs.clear()
                request.docs.extend(r_docs)

    def close(self):
        self._executor.close()
