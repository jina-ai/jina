import asyncio
from asyncio import Event, Task
from typing import Any, Callable, Dict, List, Optional

from jina import DocumentArray
from jina.types.request.data import DataRequest


class BatchQueue:
    """A batch queue that holds the data request and the callable to batch requests to."""

    def __init__(
        self,
        func: Callable,
        output_array_type: Optional[str] = None,
        params: Optional[Dict] = None,
        preferred_batch_size: int = 4,
        timeout: int = 10_000,
    ) -> None:
        self._data_lock = asyncio.Lock()
        self.func = func
        if params is None:
            params = dict()
        self._is_closed = False
        self._output_array_type = output_array_type
        self.params = params

        self._preferred_batch_size: int = preferred_batch_size
        self._timeout: int = timeout

        self._reset()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(preferred_batch_size={self._preferred_batch_size}, timeout={self._timeout})'

    def __str__(self) -> str:
        return self.__repr__()

    def _reset(self) -> None:
        """Set all events and reset the batch queue."""
        self._requests: List[DataRequest] = []
        self._request_lens: List[int] = []
        self._big_doc: DocumentArray = DocumentArray.empty()

        self._flush_trigger: Event = Event()
        self._flush_task: Optional[Task] = None
        self._timer_task: Optional[Task] = None

    def _cancel_timer_if_pending(self):
        if (
            self._timer_task
            and not self._timer_task.done()
            and not self._timer_task.cancelled()
        ):
            self._timer_task.cancel()

    def _start_timer(self):
        self._cancel_timer_if_pending()
        self._timer_task = asyncio.create_task(
            self._sleep_then_set(self._flush_trigger)
        )
        self._timer_started = True

    async def _sleep_then_set(self, event: Event):
        """Sleep and then set the event

        :param event: event to set
        """
        await asyncio.sleep(self._timeout / 1000)
        event.set()

    async def push(self, request: DataRequest) -> Task:
        """Append request to the queue. Once the request has been processed, the returned task will complete.

        :param request: The request to append to the queue.

        :return: The task that will be set once the request has been processed.
        """
        docs = request.docs

        # writes to shared data between tasks need to be mutually exclusive
        async with self._data_lock:
            if not self._flush_task:
                self._flush_task = asyncio.create_task(self._await_then_flush())
            if not self._timer_task:
                self._start_timer()

            self._big_doc.extend(docs)
            self._requests.append(request)
            self._request_lens.append(len(docs))

            if len(self._big_doc) >= self._preferred_batch_size:
                self._flush_trigger.set()

        return self._flush_task

    async def _await_then_flush(self) -> None:
        """Process all requests in the queue once flush_trigger event is set."""
        await self._flush_trigger.wait()

        # writes to shared data between tasks need to be mutually exclusive
        async with self._data_lock:
            try:

                # The function might accidentally change the size
                input_len_before_call: int = len(self._big_doc)

                # We need to get the function to process the big doc
                return_docs = await self.func(
                    docs=self._big_doc,
                    parameters=self.params,
                    docs_matrix=None,  # joining manually with batch queue is not supported right now
                    tracing_context=None,
                )

                # Output validation
                if isinstance(return_docs, DocumentArray):
                    if not len(return_docs) == input_len_before_call:
                        raise ValueError(
                            f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(return_docs)}'
                        )
                elif return_docs is None:
                    if not len(self._big_doc) == input_len_before_call:
                        raise ValueError(
                            f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(self._big_doc)}'
                        )
                else:
                    raise TypeError(
                        f'The return type must be DocumentArray / `None` when using dynamic batching, '
                        f'but getting {return_docs!r}'
                    )

                # We need to re-slice the big doc array into the original requests
                self._apply_return_docs_to_requests(return_docs)
            finally:
                self._reset()

    def _apply_return_docs_to_requests(self, return_docs: Optional[DocumentArray]):
        consumed_count: int = 0
        for request, request_len in zip(self._requests, self._request_lens):
            left = consumed_count
            right = consumed_count + request_len
            if return_docs:
                request.data.set_docs_convert_arrays(
                    return_docs[left:right], ndarray_type=self._output_array_type
                )
            else:
                request.data.set_docs_convert_arrays(
                    self._big_doc[left:right], ndarray_type=self._output_array_type
                )
            consumed_count += request_len

    async def close(self):
        """Closes the batch queue by flushing pending requests."""
        if not self._is_closed:
            # debug print amount of requests to be processed.
            self._flush_trigger.set()
            if self._flush_task:
                await self._flush_task
            self._cancel_timer_if_pending()
            self._is_closed = True
