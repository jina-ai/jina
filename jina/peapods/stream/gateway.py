import copy
import asyncio

from typing import List, AsyncIterator

from .base import BaseStreamer
from ...types.message import Message
from ..runtimes.gateway.graph.topology_graph import TopologyGraph

__all__ = ['GatewayStreamer']


class GatewayStreamer(BaseStreamer):
    """Streamer used at Gateway to stream requests/responses to/from Executors"""

    def __init__(self, args, graph: TopologyGraph, **kwargs):
        super().__init__(args, **kwargs)
        self._graph = graph

    def _handle_request(self, request: 'Request') -> 'asyncio.Future':
        """
        For zmq & grpc data requests from gateway, for each request in the iterator, we send the `Message`
        using `iolet.send_message()`.

        For websocket requests from client, for each request in the iterator, we send the request in `bytes`
        using using `iolet.send_message()`.

        Then add {<request-id>: <an-empty-future>} to the request buffer.
        This empty future is used to track the `result` of this request during `receive`.

        :param request: current request in the iterator
        :return: asyncio Future for sending message
        """
        graph = copy.deepcopy(self._graph)
        # important that the gateway needs to have an instance of the graph per request
        tasks_to_respond = []
        tasks_to_ignore = []
        for origin_node in graph.origin_nodes:
            leaf_tasks = origin_node.get_leaf_tasks(
                self._connection_pool, self._convert_to_message(request), None
            )
            # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their subtrees that unwrap all the previous tasks.
            # It starts like a chain of waiting for tasks from previous nodes
            tasks_to_respond.extend([task for ret, task in leaf_tasks if ret])
            tasks_to_ignore.extend([task for ret, task in leaf_tasks if not ret])

        async def _merge_results_at_end_gateway(
            tasks: List[asyncio.Task],
        ) -> asyncio.Future:
            from jina import DocumentArray

            # TODO: Should the order be deterministic by the graph structure, or depending on the response speed?
            # partial_responses = [await result for result in asyncio.as_completed(*tasks)]
            partial_responses = await asyncio.gather(*tasks)

            # when merging comes, one task may return None
            filtered_partial_responses = list(
                filter(lambda x: x is not None, partial_responses)
            )
            if len(filtered_partial_responses) > 1:
                docs = DocumentArray(
                    [
                        d
                        for r in filtered_partial_responses
                        for d in getattr(r.request, 'docs')
                    ]
                )
                groundtruths = DocumentArray(
                    [
                        d
                        for r in filtered_partial_responses
                        for d in getattr(r.request, 'groundtruths')
                    ]
                )
                filtered_partial_responses[0].request.docs.clear()
                filtered_partial_responses[0].request.docs.extend(docs)
                filtered_partial_responses[0].request.groundtruths.clear()
                filtered_partial_responses[0].request.groundtruths.extend(groundtruths)

            return filtered_partial_responses[0]

        return asyncio.ensure_future(_merge_results_at_end_gateway(tasks_to_respond))

    def _convert_to_message(self, request: 'Request') -> Message:
        """Convert `Request` to `Message`

        :param request: current request in the iterator
        :return: Message object
        """
        return Message(None, request, 'gateway', **vars(self.args))

    async def stream(self, request_iterator, *args) -> AsyncIterator['Request']:
        """
        stream requests from client iterator and stream responses back.

        :param request_iterator: iterator of requests
        :param args: positional arguments
        :yield: responses from Executors
        """
        async_iter: AsyncIterator = (
            self._stream_requests_with_prefetch(request_iterator, self.args.prefetch)
            if self.args.prefetch > 0
            else self._stream_requests(request_iterator)
        )

        async for response in async_iter:
            yield response

    # alias of stream used as a grpc servicer
    Call = stream
