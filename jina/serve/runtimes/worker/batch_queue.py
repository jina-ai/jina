import asyncio
from asyncio import Event, Task
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
        return self.__repr__()
    
    def _reset(self) -> None:
        """Set all events and reset the batch queue."""
        self._requests: List[DataRequest] = []
        self._request_lens: List[int] = []
        self._big_doc: DocumentArray = DocumentArray.empty()

        self._flush_trigger: Event = Event()
        self._flush_task: Task = asyncio.create_task(self.await_then_flush(self._flush_trigger))
        self._timer_started: bool = False
    
    def _start_timer(self):
        asyncio.create_task(sleep_then_set(self._timeout / 1000, self._flush_trigger))
        self._timer_started = True
    
    def push(self, request: DataRequest) -> Task:
        """Append request to the queue. Once the request has been processed, the task will be set.
        
        :param request: The request to append to the queue.

        :return: The task that will be set once the request has been processed.
        """
        if not self._timer_started:
            self._start_timer()

        docs = request.docs
        self._big_doc.extend(docs)
        self._requests.append(request)
        self._request_lens.append(len(docs))

        if len(self._big_doc) >= self._preferred_batch_size:
            self._flush_trigger.set()
        
        return self._flush_task
    
    async def await_then_flush(self, trigger_event: Event) -> None:
        """Process all requests in the queue once event is set.
        
        :param trigger_event: The event that will trigger the flush.
        """
        await trigger_event.wait()
        try:
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
                self._set_result(request, return_data[left: right], self._big_doc[left: right])
                consumed_count += request_len

            # TODO: Metrics?
            #self._record_docs_processed_monitoring(requests, docs)
            #self._record_response_size_monitoring(requests)

            self._reset()

        except Exception as e:
            # We need to reset the batch queue
            # This needs to occur even if the executor fails otherwise it will block forever
            self._reset()
            raise e

    def _set_result(self, request: DataRequest, return_data: DocumentArray, docs: DocumentArray) -> None:
        if return_data is not None:
            if isinstance(return_data, DocumentArray):
                docs = return_data
            else:
                raise TypeError(
                    f'The return type must be DocumentArray / `None` when using dynamic batching, '
                    f'but getting {return_data!r}'
                )

        request.data.set_docs_convert_arrays(docs, ndarray_type=self.args.output_array_type)
