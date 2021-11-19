import copy
import asyncio

from typing import List, TYPE_CHECKING, Callable, Union

from .graph.topology_graph import TopologyGraph
from ...networking import GrpcConnectionPool
from ....types.message import Message

if TYPE_CHECKING:
    from ....types.request import Request


def handle_request(
    graph: 'TopologyGraph', connection_pool: 'GrpcConnectionPool'
) -> Callable[['Request'], 'asyncio.Future']:
    def _handle_request(request: 'Request') -> 'asyncio.Future':

        request_graph = copy.deepcopy(graph)
        # important that the gateway needs to have an instance of the graph per request
        tasks_to_respond = []
        tasks_to_ignore = []
        for origin_node in request_graph.origin_nodes:
            leaf_tasks = origin_node.get_leaf_tasks(
                connection_pool, Message(None, request), None
            )
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
                filtered_partial_responses[0].request.docs.clear()
                filtered_partial_responses[0].request.docs.extend(docs)

            return filtered_partial_responses[0]

        return asyncio.ensure_future(_merge_results_at_end_gateway(tasks_to_respond))

    return _handle_request


def handle_result(result: Union['Message', List['Message']]):
    # TODO: Handle better the merging of messages
    if isinstance(result, List):
        return result[0].request
    elif isinstance(result, Message):
        return result.request
