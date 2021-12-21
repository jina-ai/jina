from typing import Dict, List, TYPE_CHECKING

from .... import __default_endpoint__, __default_executor__
from ....excepts import (
    ExecutorFailToLoad,
    BadConfigSource,
)
from ....executors import BaseExecutor
from .... import DocumentArray, DocumentArrayMemmap
from ....helper import reduce
from ....types.request.data import DataRequest

if TYPE_CHECKING:
    import argparse
    from ....logging.logger import JinaLogger


def get_docs_matrix_from_request(
    requests: List['DataRequest'],
    field: str,
) -> List['DocumentArray']:
    """
    Returns a docs matrix from a list of DataRequest objects.
    :param requests: List of DataRequest objects
    :param field: field to be retrieved
    :return: docs matrix: list of DocumentArray objects
    """
    if len(requests) > 1:
        result = [getattr(request, field) for request in requests]
    else:
        result = [getattr(requests[0], field)]

    # to unify all length=0 DocumentArray (or any other results) will simply considered as None
    # otherwise, the executor has to handle [None, None, None] or [DocArray(0), DocArray(0), DocArray(0)]
    len_r = sum(len(r) for r in result)
    if len_r:
        return result


def get_docs_from_request(
    requests: List['DataRequest'],
    field: str,
) -> 'DocumentArray':
    """
    Gets a field from the message

    :param requests: requests to get the field from
    :param field: field name to access

    :returns: DocumentArray extraced from the field from all messages
    """
    if len(requests) > 1:
        result = DocumentArray(
            [
                d
                for r in reversed([request for request in requests])
                for d in getattr(r, field)
            ]
        )
    else:
        result = getattr(requests[0], field)

    return result


class DataRequestHandler:
    """Object to encapsulate the code related to handle the data requests passing to executor and its returned values"""

    def __init__(self, args: 'argparse.Namespace', logger: 'JinaLogger', **kwargs):
        """Initialize private parameters and execute private loading functions.

        :param args: args from CLI
        :param logger: the logger provided by the user
        :param kwargs: extra keyword arguments
        """
        super().__init__()
        self.args = args
        self.args.pea_id = self.args.shard_id
        self.args.parallel = self.args.shards
        self.logger = logger
        self._is_closed = False
        self._load_executor()

    def _load_executor(self):
        """Load the executor to this runtime, specified by ``uses`` CLI argument."""
        try:
            self._executor = BaseExecutor.load_config(
                self.args.uses,
                uses_with=self.args.uses_with,
                uses_metas=self.args.uses_metas,
                uses_requests=self.args.uses_requests,
                runtime_args=vars(self.args),
                extra_search_paths=self.args.extra_search_paths,
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

    def handle(self, requests: List['DataRequest']) -> DataRequest:
        """Initialize private parameters and execute private loading functions.

        :param requests: The messages to handle containing a DataRequest
        :returns: the processed message
        """
        # skip executor if endpoints mismatch
        if (
            requests[0].header.exec_endpoint not in self._executor.requests
            and __default_endpoint__ not in self._executor.requests
        ):
            self.logger.debug(
                f'skip executor: mismatch request, exec_endpoint: {requests[0].header.exec_endpoint}, requests: {self._executor.requests}'
            )
            return requests[0]

        params = self._parse_params(
            requests[0].parameters.to_dict(), self._executor.metas.name
        )
        docs = get_docs_from_request(
            requests,
            field='docs',
        )

        # executor logic
        r_docs = self._executor(
            req_endpoint=requests[0].header.exec_endpoint,
            docs=get_docs_from_request(requests, field='docs'),
            parameters=params,
            docs_matrix=get_docs_matrix_from_request(
                requests,
                field='docs',
            ),
            groundtruths=get_docs_from_request(
                requests,
                field='groundtruths',
            ),
            groundtruths_matrix=get_docs_matrix_from_request(
                requests,
                field='groundtruths',
            ),
        )
        # assigning result back to request
        # 1. Return none: do nothing
        # 2. Return nonempty and non-DocumentArray: raise error
        # 3. Return DocArray, but the memory pointer says it is the same as self.docs: do nothing
        # 4. Return DocArray and its not a shallow copy of self.docs: assign self.request.docs
        if r_docs is not None:
            if isinstance(r_docs, (DocumentArray, DocumentArrayMemmap)):
                if r_docs != requests[0].docs:
                    # this means the returned DocArray is a completely new one
                    DataRequestHandler.replace_docs(requests[0], r_docs)
            elif isinstance(r_docs, dict):
                requests[0].parameters.update(r_docs)
            else:
                raise TypeError(
                    f'The return type must be DocumentArray / DocumentArrayMemmap / Dict / `None`, '
                    f'but getting {r_docs!r}'
                )
        elif len(requests) > 1:
            DataRequestHandler.replace_docs(requests[0], docs)

        return requests[0]

    @staticmethod
    def replace_docs(request, docs):
        """Replaces the docs in a message with new Documents.

        :param request: The request object
        :param docs: the new docs to be used
        """
        request.docs.clear()
        request.docs.extend(docs)

    @staticmethod
    def merge_routes(requests):
        """Merges all routes found in requests into the first message

        :param requests: The messages containing the requests with the routes to merge
        """
        if len(requests) <= 1:
            return
        existing_pod_routes = [r.pod for r in requests[0].routes]
        for request in requests[1:]:
            for route in request.routes:
                if route.pod not in existing_pod_routes:
                    requests[0].routes.append(route)
                    existing_pod_routes.append(route.pod)

    def close(self):
        """ Close the data request handler, by closing the executor """
        if not self._is_closed:
            self._executor.close()
            self._is_closed = True
