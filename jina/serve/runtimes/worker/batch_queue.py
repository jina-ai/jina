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
        self._request_docarray_cls = request_docarray_cls
        self._response_docarray_cls = response_docarray_cls
        self._preferred_batch_size: int = preferred_batch_size
        self._timeout: int = timeout
        self._reset()
        self._flush_trigger: Event = Event()
        self._timer_started, self._timer_finished = False, False
        self._timer_task: Optional[Task] = None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(preferred_batch_size={self._preferred_batch_size}, timeout={self._timeout})'

    def __str__(self) -> str:
        return self.__repr__()

    def _reset(self) -> None:
        """Set all events and reset the batch queue."""
        self._requests: List[DataRequest] = []
        # a list of every request ID
        self._request_idxs: List[int] = []
        self._request_lens: List[int] = []
        self._requests_completed: List[asyncio.Queue] = []
        if not docarray_v2:
            self._big_doc: DocumentArray = DocumentArray.empty()
        else:
            self._big_doc = self._request_docarray_cls()

        self._flush_task: Optional[Task] = None

    def _cancel_timer_if_pending(self):
        if (
            self._timer_task
            and not self._timer_task.done()
            and not self._timer_task.cancelled()
        ):
            self._timer_finished = False
            self._timer_task.cancel()

    def _start_timer(self):
        self._cancel_timer_if_pending()
        self._timer_task = asyncio.create_task(
            self._sleep_then_set()
        )

    async def _sleep_then_set(self):
        """Sleep and then set the event
        """
        self._timer_finished = False
        await asyncio.sleep(self._timeout / 1000)
        self._flush_trigger.set()
        self._timer_finished = True

    async def push(self, request: DataRequest) -> asyncio.Queue:
        """Append request to the the list of requests to be processed.

        This method creates an asyncio Queue for that request and keeps track of it. It returns
        this queue to the caller so that the caller can now when this request has been processed

        :param request: The request to append to the queue.

        :return: The queue that will receive when the request is processed.
        """
        docs = request.docs

        if not self._timer_task or self._timer_finished:
            # If there is no timer (first arrival), or the timer is already consumed, any new push should trigger a new Timer, before
            # this push requests the data lock. The order of accessing the data lock guarantees that this request will be put in the `big_doc`
            # before the `flush` task processes it.
            self._start_timer()
        async with self._data_lock:
            if not self._flush_task:
                self._flush_task = asyncio.create_task(self._await_then_flush())

            self._big_doc.extend(docs)
            next_req_idx = len(self._requests)
            num_docs = len(docs)
            self._request_idxs.extend([next_req_idx] * num_docs)
            self._request_lens.append(len(docs))
            self._requests.append(request)
            queue = asyncio.Queue()
            self._requests_completed.append(queue)
            if len(self._big_doc) >= self._preferred_batch_size:
                self._flush_trigger.set()

        return queue

    async def _await_then_flush(self) -> None:
        """Process all requests in the queue once flush_trigger event is set."""

        def _get_docs_groups_completed_request_indexes(
            non_assigned_docs,
            non_assigned_docs_reqs_idx,
            sum_from_previous_mini_batch_in_first_req_idx,
        ):
            """
            This method groups all the `non_assigned_docs` into groups of docs according to the `req_idx` they belong to.
            They are only distributed when we are sure that the request is full.

            :param non_assigned_docs: The documents that have already been processed but have not been assigned to a request result
            :param non_assigned_docs_reqs_idx: The request IDX that are not yet completed (not all of its docs have been processed)
            :param sum_from_previous_mini_batch_in_first_req_idx: The number of docs from previous iteration that belong to the first non_assigned_req_idx. This is useful to make sure we know when a request is completed.

            :return: list of document groups and a list of request Idx to which each of these groups belong
            """
            distributed_requests = []
            completed_req_idx = []
            num_distributed_docs = 0
            num_docs_in_req_idx = 0
            min_involved_req_idx = non_assigned_docs_reqs_idx[0]
            req_idx = min_involved_req_idx
            for req_idx in non_assigned_docs_reqs_idx:
                sum_from_previous_mini_batch_in_first_req_idx -= (
                    1  # the previous leftovers are being allocated here
                )
                if req_idx > min_involved_req_idx:
                    request_bucket = non_assigned_docs[
                        num_distributed_docs : num_distributed_docs
                        + num_docs_in_req_idx
                    ]
                    num_distributed_docs += num_docs_in_req_idx
                    completed_req_idx.append(min_involved_req_idx)
                    min_involved_req_idx = req_idx
                    num_docs_in_req_idx = 0
                    distributed_requests.append(request_bucket)
                num_docs_in_req_idx += 1

            if (
                req_idx not in completed_req_idx
                and num_docs_in_req_idx + sum_from_previous_mini_batch_in_first_req_idx
                == self._request_lens[req_idx]
            ):
                completed_req_idx.append(req_idx)
                request_bucket = non_assigned_docs[
                    num_distributed_docs : num_distributed_docs + num_docs_in_req_idx
                ]
                distributed_requests.append(request_bucket)

            return distributed_requests, completed_req_idx

        async def _assign_results(
            non_assigned_docs,
            non_assigned_docs_reqs_idx,
            sum_from_previous_mini_batch_in_first_req_idx,
        ):
            """
            This method aims to assign to the corresponding request objects the resulting documents from the mini batches.
            They are assigned when we are sure that the Request is fully processed.
            It also communicates to the corresponding queue that the request is full so that it can be returned

            :param non_assigned_docs: The documents that have already been processed but have not been assigned to a request result
            :param non_assigned_docs_reqs_idx: The request IDX that are not yet completed (not all of its docs have been processed)
            :param sum_from_previous_mini_batch_in_first_req_idx: The number of docs from previous iteration that belong to the first non_assigned_req_idx. This is useful to make sure we know when a request is completed.

            :return: amount of assigned documents so that some documents can come back in the next iteration
            """
            (
                docs_grouped,
                completed_req_idxs,
            ) = _get_docs_groups_completed_request_indexes(
                non_assigned_docs,
                non_assigned_docs_reqs_idx,
                sum_from_previous_mini_batch_in_first_req_idx,
            )
            num_assigned_docs = sum(len(group) for group in docs_grouped)

            for docs_group, request_idx in zip(docs_grouped, completed_req_idxs):
                request = self._requests[request_idx]
                request_completed = self._requests_completed[request_idx]
                request.data.set_docs_convert_arrays(
                    docs_group, ndarray_type=self._output_array_type
                )
                await request_completed.put(None)

            return num_assigned_docs

        def batch(iterable_1, iterable_2, n=1):
            items = len(iterable_1)
            for ndx in range(0, items, n):
                yield iterable_1[ndx : min(ndx + n, items)], iterable_2[
                    ndx : min(ndx + n, items)
                ]

        await self._flush_trigger.wait()
        # writes to shared data between tasks need to be mutually exclusive
        async with self._data_lock:
            # At this moment, we have documents concatenated in self._big_doc corresponding to requests in
            # self._requests with its lengths stored in self._requests_len. For each requests, there is a queue to
            # communicate that the request has been processed properly. At this stage the data_lock is ours and
            # therefore no-one can add requests to this list.
            self._flush_trigger: Event = Event()
            try:
                if not docarray_v2:
                    non_assigned_to_response_docs: DocumentArray = DocumentArray.empty()
                else:
                    non_assigned_to_response_docs = self._response_docarray_cls()

                non_assigned_to_response_request_idxs = []
                sum_from_previous_first_req_idx = 0
                for docs_inner_batch, req_idxs in batch(
                    self._big_doc, self._request_idxs, self._preferred_batch_size
                ):
                    involved_requests_min_indx = req_idxs[0]
                    involved_requests_max_indx = req_idxs[-1]
                    input_len_before_call: int = len(docs_inner_batch)
                    batch_res_docs = None
                    try:
                        batch_res_docs = await self.func(
                            docs=docs_inner_batch,
                            parameters=self.params,
                            docs_matrix=None,  # joining manually with batch queue is not supported right now
                            tracing_context=None,
                        )
                        # Output validation
                        if (docarray_v2 and isinstance(batch_res_docs, DocList)) or (
                            not docarray_v2
                            and isinstance(batch_res_docs, DocumentArray)
                        ):
                            if not len(batch_res_docs) == input_len_before_call:
                                raise ValueError(
                                    f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(batch_res_docs)}'
                                )
                        elif batch_res_docs is None:
                            if not len(docs_inner_batch) == input_len_before_call:
                                raise ValueError(
                                    f'Dynamic Batching requires input size to equal output size. Expected output size {input_len_before_call}, but got {len(docs_inner_batch)}'
                                )
                        else:
                            array_name = (
                                'DocumentArray' if not docarray_v2 else 'DocList'
                            )
                            raise TypeError(
                                f'The return type must be {array_name} / `None` when using dynamic batching, '
                                f'but getting {batch_res_docs!r}'
                            )
                    except Exception as exc:
                        # All the requests containing docs in this Exception should be raising it
                        for request_full in self._requests_completed[
                            involved_requests_min_indx : involved_requests_max_indx + 1
                        ]:
                            await request_full.put(exc)
                    else:
                        # We need to attribute the docs to their requests
                        non_assigned_to_response_docs.extend(batch_res_docs or docs_inner_batch)
                        non_assigned_to_response_request_idxs.extend(req_idxs)
                        num_assigned_docs = await _assign_results(
                            non_assigned_to_response_docs,
                            non_assigned_to_response_request_idxs,
                            sum_from_previous_first_req_idx,
                        )

                        sum_from_previous_first_req_idx = (
                            len(non_assigned_to_response_docs) - num_assigned_docs
                        )
                        non_assigned_to_response_docs = non_assigned_to_response_docs[
                            num_assigned_docs:
                        ]
                        non_assigned_to_response_request_idxs = (
                            non_assigned_to_response_request_idxs[num_assigned_docs:]
                        )
                if len(non_assigned_to_response_request_idxs) > 0:
                    _ = await _assign_results(
                        non_assigned_to_response_docs,
                        non_assigned_to_response_request_idxs,
                        sum_from_previous_first_req_idx,
                    )
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
