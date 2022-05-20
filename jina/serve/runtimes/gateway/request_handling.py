import asyncio
import copy
import time
from typing import TYPE_CHECKING, Callable, List, Optional

import grpc.aio
from docarray import DocumentArray

from jina.excepts import InternalNetworkError
from jina.importer import ImportExtensions
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry

    from jina.types.request import Request


class RequestHandler:
    """
    Class that handles the requests arriving to the gateway and the result extracted from the requests future.

    :param metrics_registry: optional metrics registry for prometheus used if we need to expose metrics from the executor or from the data request handler
    :param runtime_name: optional runtime_name that will be registered during monitoring
    """

    def __init__(
        self,
        metrics_registry: Optional['CollectorRegistry'] = None,
        runtime_name: Optional[str] = None,
    ):
        self._request_init_time = {} if metrics_registry else None
        self._executor_endpoint_mapping = None

        if metrics_registry:
            with ImportExtensions(
                required=True,
                help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Gauge, Summary

            self._receiving_request_metrics = Summary(
                'receiving_request_seconds',
                'Time spent processing request',
                registry=metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(runtime_name)

            self._pending_requests_metrics = Gauge(
                'number_of_pending_requests',
                'Number of pending requests',
                registry=metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(runtime_name)

        else:
            self._receiving_request_metrics = None
            self._pending_requests_metrics = None

    def handle_request(
        self, graph: 'TopologyGraph', connection_pool: 'GrpcConnectionPool'
    ) -> Callable[['Request'], 'asyncio.Future']:
        """
        Function that handles the requests arriving to the gateway. This will be passed to the streamer.

        :param graph: The TopologyGraph of the Flow.
        :param connection_pool: The connection pool to be used to send messages to specific nodes of the graph
        :return: Return a Function that given a Request will return a Future from where to extract the response
        """

        async def gather_endpoints(request_graph):
            def _get_all_nodes(node, accum, accum_names):
                if node.name not in accum_names:
                    accum.append(node)
                    accum_names.append(node.name)
                for n in node.outgoing_nodes:
                    _get_all_nodes(n, accum, accum_names)
                return accum, accum_names

            nodes = []
            node_names = []
            for origin_node in request_graph.origin_nodes:
                subtree_nodes, subtree_node_names = _get_all_nodes(origin_node, [], [])
                for st_node, st_node_name in zip(subtree_nodes, subtree_node_names):
                    if st_node_name not in node_names:
                        nodes.append(st_node)
                        node_names.append(st_node_name)
            try:
                tasks_to_get_endpoints = [
                    node.get_endpoints(connection_pool) for node in nodes
                ]
                endpoints = await asyncio.gather(*tasks_to_get_endpoints)
            except InternalNetworkError as err:
                err_code = err.code()
                if err_code == grpc.StatusCode.UNAVAILABLE:
                    err._details = (
                        err.details()
                        + f' |Gateway: Communication error with deployment at address(es) {err.dest_addr}. Head or worker(s) may be down.'
                    )
                    raise err
                else:
                    raise

            self._executor_endpoint_mapping = {}
            for node, (endp, _) in zip(nodes, endpoints):
                self._executor_endpoint_mapping[node.name] = endp.endpoints

        def _handle_request(request: 'Request') -> 'asyncio.Future':
            if self._receiving_request_metrics:
                self._request_init_time[request.request_id] = time.time()
            if self._pending_requests_metrics:
                self._pending_requests_metrics.inc()
            # important that the gateway needs to have an instance of the graph per request
            request_graph = copy.deepcopy(graph)

            if graph.has_filter_conditions:
                request_doc_ids = request.data.docs[
                    :, 'id'
                ]  # used to maintain order of docs that are filtered by executors
            tasks_to_respond = []
            tasks_to_ignore = []
            endpoint = request.header.exec_endpoint
            r = request.routes.add()
            r.executor = 'gateway'
            r.start_time.GetCurrentTime()
            # If the request is targeting a specific deployment, we can send directly to the deployment instead of
            # querying the graph
            for origin_node in request_graph.origin_nodes:
                leaf_tasks = origin_node.get_leaf_tasks(
                    connection_pool,
                    request,
                    None,
                    endpoint=endpoint,
                    executor_endpoint_mapping=self._executor_endpoint_mapping,
                    target_executor_pattern=request.header.target_executor,
                )
                # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their
                # subtrees that unwrap all the previous tasks. It starts like a chain of waiting for tasks from previous
                # nodes
                tasks_to_respond.extend([task for ret, task in leaf_tasks if ret])
                tasks_to_ignore.extend([task for ret, task in leaf_tasks if not ret])

            def _sort_response_docs(response):
                # sort response docs according to their order in the initial request
                def sort_by_request_order(doc):
                    if doc.id in request_doc_ids:
                        return request_doc_ids.index(doc.id)
                    else:
                        return len(request_doc_ids)  # put new/unknown docs at the end

                sorted_docs = sorted(response.data.docs, key=sort_by_request_order)
                response.data.docs = DocumentArray(sorted_docs)

            async def _process_results_at_end_gateway(
                tasks: List[asyncio.Task], request_graph: TopologyGraph
            ) -> asyncio.Future:
                if self._executor_endpoint_mapping is None:
                    await asyncio.gather(gather_endpoints(request_graph))

                partial_responses = await asyncio.gather(*tasks)
                partial_responses, metadatas = zip(*partial_responses)
                filtered_partial_responses = list(
                    filter(lambda x: x is not None, partial_responses)
                )

                response = filtered_partial_responses[0]
                request_graph.add_routes(response)

                if graph.has_filter_conditions:
                    _sort_response_docs(response)

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

    def handle_result(self) -> Callable[['Request'], 'asyncio.Future']:
        """
        Function that handles the result when extracted from the request future

        :return: Return a Function that returns a request to be returned to the client
        """

        def _handle_result(result: 'Request'):
            """
            Function that handles the result when extracted from the request future

            :param result: The result returned to the gateway. It extracts the request to be returned to the client
            :return: Returns a request to be returned to the client
            """

            for route in result.routes:
                if route.executor == 'gateway':
                    route.end_time.GetCurrentTime()

            if self._receiving_request_metrics:
                init_time = self._request_init_time.pop(
                    result.request_id
                )  # need to pop otherwise it stays in memory forever
                self._receiving_request_metrics.observe(time.time() - init_time)

            if self._pending_requests_metrics:
                self._pending_requests_metrics.dec()

            return result

        return _handle_result
