import asyncio
from asyncio import Event, Task
from typing import Any, Dict, List, Optional

from jina import DocumentArray
from jina.serve.executors import BaseExecutor
from jina.types.request.data import DataRequest


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
        self._flush_task = asyncio.create_task(self._await_then_flush())
        self._timer_task: Optional[Task] = None

    def _start_timer(self):
        if (
            self._timer_task
            and not self._timer_task.done()
            and not self._timer_task.cancelled()
        ):
            self._timer_task.cancel()
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

        if not self._timer_task:
            self._start_timer()

        docs = request.docs
        # TODO: is this protected/synchronous ?
        self._big_doc.extend(docs)
        self._requests.append(request)
        self._request_lens.append(len(docs))

        if len(self._big_doc) >= self._preferred_batch_size:
            self._flush_trigger.set()

        return self._flush_task

    async def _await_then_flush(self) -> None:
        """Process all requests in the queue once flush_trigger event is set."""
        await self._flush_trigger.wait()
        try:
            # The executor might accidentally change the size
            input_len_before_call: int = len(self._big_doc)

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
            # debug print amount of requests to be processed.
            self._flush_trigger.set()
            # await tasks here
            self._is_closed = True
