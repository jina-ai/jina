import asyncio
from asyncio import Event, Task
from typing import Any, Dict, List, Optional

from jina import DocumentArray
from jina.serve.executors import BaseExecutor
from jina.types.request.data import DataRequest


async def sleep_then_set(time_seconds: float, event: Event):
    """Sleep for time_seconds and then set the event

    :param time_seconds: time to sleep
    :param event: event to set
    """
    await asyncio.sleep(time_seconds)
    event.set()


class BatchQueue:
    """A batch queue that holds the data request and the executor."""

    def __init__(
        self,
        executor: BaseExecutor,
        exec_endpoint: str,
        args: Any,
        params: Optional[Dict] = None,
        preferred_batch_size: int = 4,
        timeout: int = 10_000,
        max_batch_size: Optional[int] = None,
    ) -> None:
        if params is None:
            params = dict()
        self._is_closed = False
        self._executor: BaseExecutor = executor
        self._exec_endpoint: str = exec_endpoint
        self.args = args
        self.params = params

        self._preferred_batch_size: int = preferred_batch_size
        self._timeout: int = timeout
        self._max_batch_size: Optional[int] = max_batch_size
        if self._max_batch_size:
            if self._max_batch_size < self._preferred_batch_size:
                raise ValueError(
                    f'Max batch size must be greater than or equal to preferred batch size.'
                    f'Got max batch size {self._max_batch_size} and preferred'
                    f'batch size {self._preferred_batch_size}'
                )

        self._reset()

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}({self._executor}, {self._exec_endpoint},'
            f'preferred_batch_size={self._preferred_batch_size}, timeout={self._timeout})'
        )

    def __str__(self) -> str:
        return self.__repr__()

    def _reset(self) -> None:
        """Set all events and reset the batch queue."""
        self._requests: List[DataRequest] = []
        self._request_lens: List[int] = []
        self._big_doc: DocumentArray = DocumentArray.empty()

        self._flush_trigger: Event = Event()
        self._flush_task = asyncio.create_task(
            self.await_then_flush(self._flush_trigger)
        )
        self._timer_started: bool = False

    def _start_timer(self):
        # TODO: make sure to cancel old timer task before starting the new one
        asyncio.create_task(sleep_then_set(self._timeout / 1000, self._flush_trigger))
        self._timer_started = True

    async def push(self, request: DataRequest) -> Task:
        """Append request to the queue. Once the request has been processed, the returned task will complete.

        :param request: The request to append to the queue.

        :return: The task that will be set once the request has been processed.
        """
        if self._max_batch_size:
            if len(self._big_doc) + len(request.docs) > self._max_batch_size:
                self._flush_trigger.set()
                await self._flush_task

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
            # The executor might accidentally change the size
            input_len_before_call: int = len(self._big_doc)

            if self._max_batch_size:
                if input_len_before_call > self._max_batch_size:
                    # TODO: We might want to have the batch queue split the request up instead
                    # TODO(johannes): update the docstring of the decorator to reflect this
                    raise ValueError(
                        f'Input length {input_len_before_call} is greater than max batch size {self._max_batch_size}'
                    )

            # We need to get the executor to process the big doc
            return_data = await self._executor.__acall__(
                req_endpoint=self._exec_endpoint,
                docs=self._big_doc,
                parameters=self.params,
                docs_matrix=None,  # joining manually with batch queue is not supported right now
                # TO GIRISH: The tracing seems to work already.
                # Do we need to pass this?
                # The only difference I can see is that the nesting level is different.
                tracing_context=None,
            )

            # Output validation
            # TODO: raise exception instead of using assert
            if isinstance(return_data, DocumentArray):
                assert (
                    len(return_data) == input_len_before_call
                ), f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(return_data)}'
            elif return_data is None:
                assert (
                    len(self._big_doc) == input_len_before_call
                ), f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(self._big_doc)}'
            else:
                raise TypeError(
                    f'The return type must be DocumentArray / `None` when using dynamic batching, '
                    f'but getting {return_data!r}'
                )

            # We need to reslice the big doc array into the original requests
            self._fan_out_return_data(return_data)

            self._reset()

        except Exception as e:
            # We need to reset the batch queue
            # This needs to occur even if the executor fails otherwise it will block forever
            self._reset()
            raise e

    def _fan_out_return_data(self, return_data: Optional[DocumentArray]):
        consumed_count: int = 0
        for request, request_len in zip(self._requests, self._request_lens):
            left = consumed_count
            right = consumed_count + request_len
            if return_data:
                request.data.set_docs_convert_arrays(
                    return_data[left:right], ndarray_type=self.args.output_array_type
                )
            else:
                request.data.set_docs_convert_arrays(
                    self._big_doc[left:right], ndarray_type=self.args.output_array_type
                )
            consumed_count += request_len

    async def close(self):
        """Closes the batch queue by flushing pending requests."""
        if not self._is_closed:
            self._flush_trigger.set()
            self._is_closed = True
