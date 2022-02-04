import copy
import asyncio

from typing import List, TYPE_CHECKING, Callable

from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph
from jina.serve.networking import GrpcConnectionPool

if TYPE_CHECKING:
    from jina.types.request import Request


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
        endpoint = request.header.exec_endpoint
        r = request.routes.add()
        r.executor = 'gateway'
        r.start_time.GetCurrentTime()
        # If the request is targeting a specific deployment, we can send directly to the deployment instead of querying the graph
        if request.header.target_executor:
            tasks_to_respond.extend(
                connection_pool.send_request(
                    request=request,
                    deployment=request.header.target_executor,
                    head=True,
                    endpoint=endpoint,
                )
            )
        else:
            for origin_node in request_graph.origin_nodes:
                leaf_tasks = origin_node.get_leaf_tasks(
                    connection_pool, request, None, endpoint=endpoint
                )
                # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their
                # subtrees that unwrap all the previous tasks. It starts like a chain of waiting for tasks from previous
                # nodes
                tasks_to_respond.extend([task for ret, task in leaf_tasks if ret])
                tasks_to_ignore.extend([task for ret, task in leaf_tasks if not ret])

        async def _process_results_at_end_gateway(
            tasks: List[asyncio.Task], request_graph: TopologyGraph
        ) -> asyncio.Future:

            partial_responses = await asyncio.gather(*tasks)
            partial_responses, metadatas = zip(*partial_responses)
            filtered_partial_responses = list(
                filter(lambda x: x is not None, partial_responses)
            )

            response = filtered_partial_responses[0]
            request_graph.add_routes(response)

            return response

        # In case of empty topologies
        if not tasks_to_respond:
            r.end_time.GetCurrentTime()
            future = asyncio.Future()
            future.set_result((request, {}))
            tasks_to_respond.append(future)
        return asyncio.ensure_future(
            _process_results_at_end_gateway(tasks_to_respond, request_graph)
        )

    return _handle_request


def handle_result(result: 'Request'):
    """
    Function that handles the result when extracted from the request future

    :param result: The result returned to the gateway. It extracts the request to be returned to the client
    :return: Returns a request to be returned to the client
    """
    for route in result.routes:
        if route.executor == 'gateway':
            route.end_time.GetCurrentTime()
    return result
