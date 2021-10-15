import re
from typing import Dict, List, Optional, TYPE_CHECKING

from .... import __default_endpoint__
from ....excepts import (
    ExecutorFailToLoad,
    BadConfigSource,
)
from ....executors import BaseExecutor
from ....helper import typename
from ....types.arrays.document import DocumentArray
from ....types.arrays.abstract import AbstractDocumentArray
from ....types.message import Message, Request

if TYPE_CHECKING:
    import argparse
    from ....logging.logger import JinaLogger


def _get_docs_matrix_from_message(
    msg: 'Message',
    partial_request: Optional[List[Request]],
    field: str,
) -> List['DocumentArray']:
    if partial_request is not None:
        result = [getattr(r, field) for r in reversed(partial_request)]
    else:
        result = [getattr(msg.request, field)]

    # to unify all length=0 DocumentArray (or any other results) will simply considered as None
    # otherwise, the executor has to handle [None, None, None] or [DocArray(0), DocArray(0), DocArray(0)]
    len_r = sum(len(r) for r in result)
    if len_r:
        return result


def _get_docs_from_msg(
    msg: 'Message',
    partial_request: Optional[List[Request]],
    field: str,
) -> 'DocumentArray':
    if partial_request is not None:
        result = DocumentArray(
            [d for r in reversed(partial_request) for d in getattr(r, field)]
        )
    else:
        result = getattr(msg.request, field)

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
        self._load_executor()

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
        msg: 'Message',
        partial_requests: Optional[List[Request]],
        peapod_name: str,
    ):
        """Initialize private parameters and execute private loading functions.

        :param msg: The message to handle containing a DataRequest
        :param partial_requests: All the partial requests, to be considered when more than one expected part
        :param peapod_name: the name of the peapod owning this handler
        """
        # skip executor if target_peapod mismatch
        if not re.match(msg.envelope.header.target_peapod, peapod_name):
            self.logger.debug(
                f'skip executor: mismatch target, target: {msg.envelope.header.target_peapod}, name: {peapod_name}'
            )
            return

        # skip executor if endpoints mismatch
        if (
            msg.envelope.header.exec_endpoint not in self._executor.requests
            and __default_endpoint__ not in self._executor.requests
        ):
            self.logger.debug(
                f'skip executor: mismatch request, exec_endpoint: {msg.envelope.header.exec_endpoint}, requests: {self._executor.requests}'
            )
            if partial_requests:
                DataRequestHandler.replace_docs(
                    msg,
                    docs=_get_docs_from_msg(
                        msg,
                        partial_request=partial_requests,
                        field='docs',
                    ),
                )
            return

        params = self._parse_params(msg.request.parameters, self._executor.metas.name)
        docs = _get_docs_from_msg(
            msg,
            partial_request=partial_requests,
            field='docs',
        )
        # executor logic
        r_docs = self._executor(
            req_endpoint=msg.envelope.header.exec_endpoint,
            docs=docs,
            parameters=params,
            docs_matrix=_get_docs_matrix_from_message(
                msg,
                partial_request=partial_requests,
                field='docs',
            ),
            groundtruths=_get_docs_from_msg(
                msg,
                partial_request=partial_requests,
                field='groundtruths',
            ),
            groundtruths_matrix=_get_docs_matrix_from_message(
                msg,
                partial_request=partial_requests,
                field='groundtruths',
            ),
        )

        # assigning result back to request
        # 1. Return none: do nothing
        # 2. Return nonempty and non-DocumentArray: raise error
        # 3. Return DocArray, but the memory pointer says it is the same as self.docs: do nothing
        # 4. Return DocArray and its not a shallow copy of self.docs: assign self.request.docs
        if r_docs is not None:
            if not isinstance(r_docs, AbstractDocumentArray):
                raise TypeError(
                    f'return type must be {DocumentArray!r} or None, but getting {typename(r_docs)}'
                )
            elif r_docs != msg.request.docs:
                # this means the returned DocArray is a completely new one
                DataRequestHandler.replace_docs(msg, r_docs)
        elif partial_requests:
            DataRequestHandler.replace_docs(msg, docs)

    @staticmethod
    def replace_docs(msg, docs):
        """Replaces the docs in a message with new Documents.

        :param msg: The message object
        :param docs: the new docs to be used
        """
        msg.request.docs.clear()
        msg.request.docs.extend(docs)

    def close(self):
        """ Close the data request handler, by closing the executor """
        self._executor.close()
