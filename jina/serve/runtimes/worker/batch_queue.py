import asyncio
from asyncio import Event, Task
from typing import Callable, Dict, List, Optional, TYPE_CHECKING
from jina._docarray import docarray_v2

if not docarray_v2:
    from docarray import DocumentArray
else:
    from docarray import DocList
from jina.types.request.data import DataRequest

if TYPE_CHECKING:
    from jina._docarray import DocumentArray


class BatchQueue:
    """A batch queue that holds the data request and the callable to batch requests to."""

    def __init__(
            self,
            func: Callable,
            request_docarray_cls,
            response_docarray_cls,
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
        self._docarray_cls = request_docarray_cls
        self._out_docarray_cls = response_docarray_cls
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
        self._requests_full: List[asyncio.Queue] = []
        if not docarray_v2:
            self._big_doc: DocumentArray = DocumentArray.empty()
        else:
            self._big_doc = self._docarray_cls()

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

    async def push(self, request: DataRequest) -> asyncio.Queue:
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
            queue = asyncio.Queue()
            self._requests_full.append(queue)
            if len(self._big_doc) >= self._preferred_batch_size:
                self._flush_trigger.set()

        return queue

    async def _await_then_flush(self) -> None:
        """Process all requests in the queue once flush_trigger event is set."""

        def _distribute_documents(inner_docs, requests_len_list):
            # Create an iterator to iterate over the documents
            num_distributed_docs = 0
            # Initialize a list to store the distributed requests
            distributed_requests = []

            for request_len in requests_len_list:
                # Create a new request bucket
                if num_distributed_docs + request_len <= len(inner_docs):
                    request_bucket = inner_docs[num_distributed_docs: num_distributed_docs + request_len]
                    num_distributed_docs += request_len

                    if len(request_bucket) == request_len:
                        # Add the request bucket to the list of distributed requests
                        distributed_requests.append(request_bucket)
                else:
                    break

            return distributed_requests, num_distributed_docs

        def batch(iterable, n=1):
            items = len(iterable)
            for ndx in range(0, items, n):
                yield iterable[ndx: min(ndx + n, items)]

        await self._flush_trigger.wait()
        # writes to shared data between tasks need to be mutually exclusive
        async with self._data_lock:
            # At this moment, we have documents concatenated in self._big_doc corresponding to requests in
            # self._requests with its lengths stored in self._requests_len. For each requests, there is a queue to
            # communicate that the request has been processed properly. At this stage the data_lock is ours and
            # therefore noone can add requests to this list.
            filled_requests = 0
            try:
                if not docarray_v2:
                    non_distributed_docs: DocumentArray = DocumentArray.empty()
                else:
                    non_distributed_docs = self._out_docarray_cls()
                for docs in batch(self._big_doc, self._preferred_batch_size):
                    input_len_before_call: int = len(docs)
                    try:
                        batch_res_docs = await self.func(
                            docs=docs,
                            parameters=self.params,
                            docs_matrix=None,  # joining manually with batch queue is not supported right now
                            tracing_context=None,
                        )

                        # Output validation
                        if (docarray_v2 and isinstance(batch_res_docs, DocList)) or (
                                not docarray_v2 and isinstance(batch_res_docs, DocumentArray)):
                            if not len(batch_res_docs) == input_len_before_call:
                                raise ValueError(
                                    f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(batch_res_docs)}'
                                )
                        elif batch_res_docs is None:
                            if not len(docs) == input_len_before_call:
                                raise ValueError(
                                    f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(docs)}'
                                )
                        else:
                            array_name = 'DocumentArray' if not docarray_v2 else 'DocList'
                            raise TypeError(
                                f'The return type must be {array_name} / `None` when using dynamic batching, '
                                f'but getting {batch_res_docs!r}'
                            )

                        output_executor_docs = batch_res_docs if batch_res_docs is not None else docs

                        # We need to attribute the docs to their requests
                        non_distributed_docs.extend(output_executor_docs)
                        request_buckets, num_distributed_docs_in_batch = _distribute_documents(non_distributed_docs,
                                                                                               self._request_lens[
                                                                                               filled_requests:])
                        if num_distributed_docs_in_batch > 0:
                            for bucket, request, request_full in zip(request_buckets, self._requests[filled_requests:],
                                                                     self._requests_full[filled_requests:]):
                                request.data.set_docs_convert_arrays(
                                    bucket, ndarray_type=self._output_array_type
                                )
                                await request_full.put(None)

                            filled_requests += len(request_buckets)
                            non_distributed_docs = non_distributed_docs[
                                                   num_distributed_docs_in_batch:]
                    except Exception as exc:
                        # All the requests containing docs in this Exception should be raising it
                        # TODO: Handle exceptions properly
                        for request_full in self._requests_full[filled_requests:]:
                            await request_full.put(exc)
            finally:
                self._reset()

    async def close(self):
        """Closes the batch queue by flushing pending requests."""
        if not self._is_closed:
            # debug print amount of requests to be processed.
            self._flush_trigger.set()
            if self._flush_task:
                await self._flush_task
            self._cancel_timer_if_pending()
            self._is_closed = True
