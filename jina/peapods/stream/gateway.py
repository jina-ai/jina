import copy
import argparse
import asyncio

from typing import TYPE_CHECKING, AsyncIterator

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
        return tasks_to_respond[0]

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
