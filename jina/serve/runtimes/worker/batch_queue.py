import asyncio
from asyncio import Event
from typing import List, Dict, Any

from jina import DocumentArray
from jina.serve.executors import BaseExecutor
from jina.types.request.data import DataRequest

# TODO: Make sure we dont deserialize the request twice
# TODO: SIGINT/SIGTEM: Flush

async def sleep_then_set(time_seconds: int, event: Event):
    """Sleep for time_seconds and then set the event
    
    :param time_seconds: time to sleep
    :param event: event to set
    """
    await asyncio.sleep(time_seconds)
    event.set()

class BatchQueue():
    """A batch queue that holds the data request and the executor."""

    def __init__(self, executor: BaseExecutor, exec_endpoint: str, args: Any, preferred_batch_size: int=4, timeout: int=10_000) -> None:
        self._preferred_batch_size: int = preferred_batch_size
        self._timeout: int = timeout
        self._executor: BaseExecutor = executor
        self._exec_endpoint: str = exec_endpoint
        self.args = args

        self._reset()
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._executor}, {self._exec_endpoint}, preferred_batch_size={self._preferred_batch_size}, timeout={self._timeout})'
    
    def __str__(self) -> str:
        self.__repr__()
    
    def _reset(self) -> None:
        """Set all events and reset the batch queue."""
        self._requests: List[DataRequest] = []
        self._request_lens: List[int] = []
        self._big_doc: DocumentArray = DocumentArray.empty()

        self._flush_trigger: Event = Event()
        asyncio.create_task(self.flush(self._flush_trigger))
        self._timer_started = False
        self._after_flush_event = Event()
    
    def _start_timer(self):
        asyncio.create_task(sleep_then_set(self._timeout / 1000, self._flush_trigger))
        self._timer_started = True
    
    def _reset_timeout(self) -> None:
        """Reset the timeout event."""
        self._timeout_event.set()
        self._timeout_event = Event()
    
    async def push(self, request: DataRequest) -> Event:
        """Append request to the queue. Once the request has been processed, the event will be set.
        
        :param request: The request to append to the queue.

        :return: The event that will be set once the request has been processed.
        """
        # TODO: What if timer ends and triggers the flush in the middle of this function? Is that possible?
        # This function is blocking and thus should be atomic right?
        if not self._timer_started:
            self._start_timer()

        docs = BatchQueue.get_docs_from_request(
            [request],
            field='docs',
        )

        self._big_doc.extend(docs)
        self._requests.append(request)
        self._request_lens.append(len(docs))

        if len(self._big_doc) >= self._preferred_batch_size:
            self._flush_trigger.set()
        
        return self._after_flush_event
    
    async def flush(self, trigger_event: Event) -> None:
        """Process all requests in the queue once event is set."""
        await trigger_event.wait()
        # We need to get the executor to process the big doc
        return_data = await self._executor.__acall__(
            req_endpoint=self._exec_endpoint,
            docs=self._big_doc,
            parameters={},
            docs_matrix=None,
            tracing_context=None, # TODO: Tracing?
        )

        # We need to reslice the big doc array into the original requests
        consumed_count: int = 0
        for request, request_len in zip(self._requests, self._request_lens):
            left = consumed_count
            right = consumed_count + request_len
            self._set_result([request], return_data[left: right], self._big_doc[left: right])
            consumed_count += request_len

        # TODO: Metrics?
        #self._record_docs_processed_monitoring(requests, docs)
        #self._record_response_size_monitoring(requests)

        # We need to set the after flush event and reset the batch queue
        self._after_flush_event.set()
        self._reset()

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
    # TODO: Missing some self stuff
    def _set_result(self, requests, return_data, docs):
        # assigning result back to request
        if return_data is not None:
            if isinstance(return_data, DocumentArray):
                docs = return_data
            # TODO: We will handle this later
            #elif isinstance(return_data, dict):
                #params = requests[0].parameters
                #results_key = self._KEY_RESULT

                #if not results_key in params.keys():
                    #params[results_key] = dict()

                #params[results_key].update({self.args.name: return_data})
                #requests[0].parameters = params

            else:
                raise TypeError(
                    f'The return type must be DocumentArray / Dict / `None`, '
                    f'but getting {return_data!r}'
                )

        BatchQueue.replace_docs(
            requests[0], docs, self.args.output_array_type
        )
        return docs

    # TODO: Duplicate from WorkerRequestHandler
    @staticmethod
    def replace_docs(
            request: DataRequest, docs: 'DocumentArray', ndarrray_type: str = None
    ) -> None:
        """Replaces the docs in a message with new Documents.

        :param request: The request object
        :param docs: the new docs to be used
        :param ndarrray_type: type tensor and embedding will be converted to
        """
        request.data.set_docs_convert_arrays(docs, ndarray_type=ndarrray_type)
