import copy
import asyncio

from typing import List, TYPE_CHECKING, Callable, Union

from .graph.topology_graph import TopologyGraph
from ..request_handlers.data_request_handler import DataRequestHandler
from ...networking import GrpcConnectionPool

if TYPE_CHECKING:
    from ....types.request import Request


def handle_request(
    graph: 'TopologyGraph', connection_pool: 'GrpcConnectionPool'
) -> Callable[['Request'], 'asyncio.Future']:
    """
    Function that handles the requests arriving to the gateway. This will be passed to the streamer.

    :param graph: The TopologyGraph of the Flow.
    :param connection_pool: The connection pool to be used to send messages to specific nodes of the graph
    :return: Return a Function that given a Request will return a Future from where to extract the response
    """

    def _handle_request(request: 'Request') -> 'asyncio.Future':

        request_graph = copy.deepcopy(graph)
        # important that the gateway needs to have an instance of the graph per request
        tasks_to_respond = []
        tasks_to_ignore = []
        r = request.routes.add()
        r.pod = 'gateway'
        r.start_time.GetCurrentTime()
        # If the request is targeting a specific pod, we can send directly to the pod instead of querying the graph
        if request.header.target_peapod:
            tasks_to_respond.extend(
                connection_pool.send_request(
                    request=request,
                    pod=request.header.target_peapod,
                    head=True,
                )
            )
        else:
            for origin_node in request_graph.origin_nodes:
                leaf_tasks = origin_node.get_leaf_tasks(connection_pool, request, None)
                # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their
                # subtrees that unwrap all the previous tasks. It starts like a chain of waiting for tasks from previous
                # nodes
                tasks_to_respond.extend([task for ret, task in leaf_tasks if ret])
                tasks_to_ignore.extend([task for ret, task in leaf_tasks if not ret])

        async def _merge_results_at_end_gateway(
            tasks: List[asyncio.Task],
        ) -> asyncio.Future:
            from .... import DocumentArray

            # TODO: Should the order be deterministic by the graph structure, or depending on the response speed?
            partial_responses = await asyncio.gather(*tasks)
            partial_responses, metadatas = zip(*partial_responses)
            # when merging comes, one task may return None
            filtered_partial_responses = list(
                filter(lambda x: x is not None, partial_responses)
            )
            if len(filtered_partial_responses) > 1:
                docs = DocumentArray(
                    [d for r in filtered_partial_responses for d in getattr(r, 'docs')]
                )
                filtered_partial_responses[0].docs.clear()
                filtered_partial_responses[0].docs.extend(docs)

                DataRequestHandler.merge_routes(filtered_partial_responses)

            return filtered_partial_responses[0]

        # In case of empty topologies
        if not tasks_to_respond:
            r.end_time.GetCurrentTime()
            future = asyncio.Future()
            future.set_result(request)
            tasks_to_respond.append(future)
        return asyncio.ensure_future(_merge_results_at_end_gateway(tasks_to_respond))

    return _handle_request


def handle_result(result: 'Request'):
    """
    Function that handles the result when extracted from the request future

    :param result: The result returned to the gateway. It extracts the request to be returned to the client
    :return: Returns a request to be returned to the client
    """
    for route in result.routes:
        if route.pod == 'gateway':
            route.end_time.GetCurrentTime()
    return result
