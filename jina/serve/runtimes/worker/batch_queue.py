from typing import List, Dict

from jina import DocumentArray
from jina.serve.executors import BaseExecutor
from jina.types.request.data import DataRequest

# TODO: Make sure we dont deserialize the request twice
# TODO: SIGINT/SIGTEM: Flush

class BatchQueue():
    """A batch queue that holds the data request and the executor."""

    def __init__(self, executor: BaseExecutor, exec_endpoint: str, preferred_batch_size: int=4, timeout: int=10_000) -> None:
        self._preferred_batch_size: int = preferred_batch_size
        self._timeout: int = timeout
        self._executor: BaseExecutor = executor
        self._exec_endpoint: str = exec_endpoint

        self._reset()
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._executor}, {self._exec_endpoint}, preferred_batch_size={self._preferred_batch_size}, timeout={self._timeout})'
    
    def __str__(self) -> str:
        self.__repr__()
    
    def _reset(self) -> None:
        self._requests: List[DataRequest] = []
        self._request_lens: List[int] = []
        self._big_doc: DocumentArray = DocumentArray.empty()
    
    async def push(self, request: DataRequest) -> None:
        docs = BatchQueue.get_docs_from_request(
            [request],
            field='docs',
        )

        self._big_doc.extend(docs)
        self._requests.append(request)
        self._request_lens.append(len(docs))

        if len(self._big_doc) > self._preferred_batch_size:
            await self.flush()
    
    async def flush(self) -> None:
        # executor logic
        # TODO: What if they have different params? Should we disallow params?
        # params = self._parse_params(requests[0].parameters, self._executor.metas.name)
        return_data = await self._executor.__acall__(
            req_endpoint=self._exec_endpoint,
            docs=docs,
            parameters={},
            #docs_matrix=BatchQueue.get_docs_matrix_from_request(
                #requests,
                #field='docs',
            #),
            docs_matrix=[self._big_doc], # TODO: What is docs_matrix? Another thing to ban?
            tracing_context=None, # TODO: Tracing?
        )

        # TODO: fan out big doc to all requests
        #docs = self._set_result(requests, return_data, docs)
        consumed_count: int = 0
        for request, request_len in zip(self._requests, self._request_lens):
            # TODO: What is return_data? Can we slice this? Do we need to?
            self._set_result([request], return_data, self._big_doc[consumed_count:consumed_count + request_len])
            consumed_count += request_len

        # TODO: Metrics?
        #self._record_docs_processed_monitoring(requests, docs)
        #self._record_response_size_monitoring(requests)

        return requests[0]


    # TODO: Duplicate from WorkerRequestHandler
    # TODO: This is only ever called with field='docs'
    # TODO: This is a convoluted method that should be simplified
    @staticmethod
    def get_docs_from_request(
        requests: List['DataRequest'],
        field: str,
    ) -> 'DocumentArray':
        """
        Gets a field from the message

        :param requests: requests to get the field from
        :param field: field name to access

        :returns: DocumentArray extracted from the field from all messages
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

    # TODO: Duplicate from WorkerRequestHandler
    @staticmethod
    def _parse_params(parameters: Dict, executor_name: str):
        parsed_params = parameters
        specific_parameters = parameters.get(executor_name, None)
        if specific_parameters:
            parsed_params.update(**specific_parameters)

        return parsed_params

    # TODO: Duplicate from WorkerRequestHandler
    # TODO: This is only ever called with field='docs'
    @staticmethod
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
        # TODO: The if else is redundant
        if len(requests) > 1:
            result = [getattr(request, field) for request in requests]
        else:
            result = [getattr(requests[0], field)]

        # to unify all length=0 DocumentArray (or any other results) will simply considered as None
        # otherwise, the executor has to handle [None, None, None] or [DocArray(0), DocArray(0), DocArray(0)]
        len_r = sum(len(r) for r in result)
        if len_r:
            return result


    # TODO: Duplicate from WorkerRequestHandler
    # TODO: Missing some self stuff
    def _set_result(self, requests, return_data, docs):
        # assigning result back to request
        if return_data is not None:
            if isinstance(return_data, DocumentArray):
                docs = return_data
            elif isinstance(return_data, dict):
                params = requests[0].parameters
                results_key = self._KEY_RESULT

                if not results_key in params.keys():
                    params[results_key] = dict()

                params[results_key].update({self.args.name: return_data})
                requests[0].parameters = params

            else:
                raise TypeError(
                    f'The return type must be DocumentArray / Dict / `None`, '
                    f'but getting {return_data!r}'
                )

        WorkerRequestHandler.replace_docs(
            requests[0], docs, self.args.output_array_type
        )
        return docs
