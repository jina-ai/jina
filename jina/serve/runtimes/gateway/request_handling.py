import asyncio
import copy
import time
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

import grpc.aio
from docarray import DocumentArray

from jina.excepts import InternalNetworkError
from jina.importer import ImportExtensions
from jina.proto import jina_pb2
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph
from jina.serve.runtimes.helper import _is_param_for_specific_executor
from jina.serve.runtimes.request_handlers.data_request_handler import DataRequestHandler

if TYPE_CHECKING: # pragma: no cover
    from asyncio import Future

    from opentelemetry.metrics import Meter
    from prometheus_client import CollectorRegistry

    from jina.types.request import Request


class MonitoringRequestMixin:
    """
    Mixin for the request handling monitoring

    :param metrics_registry: optional metrics registry for prometheus used if we need to expose metrics from the executor or from the data request handler
    :param runtime_name: optional runtime_name that will be registered during monitoring
    """

    def __init__(
        self,
        metrics_registry: Optional['CollectorRegistry'] = None,
        meter: Optional['Meter'] = None,
        runtime_name: Optional[str] = None,
    ):

        self._request_init_time = {} if metrics_registry else None
        self._meter_request_init_time = {} if meter else None

        if metrics_registry:
            with ImportExtensions(
                required=True,
                help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Counter, Gauge, Summary

                from jina.serve.monitoring import _SummaryDeprecated

            self._receiving_request_metrics = Summary(
                'receiving_request_seconds',
                'Time spent processing successful request',
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

            self._failed_requests_metrics = Counter(
                'failed_requests',
                'Number of failed requests',
                registry=metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(runtime_name)

            self._successful_requests_metrics = Counter(
                'successful_requests',
                'Number of successful requests',
                registry=metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(runtime_name)

            self._request_size_metrics = _SummaryDeprecated(
                old_name='request_size_bytes',
                name='received_request_bytes',
                documentation='The size in bytes of the request returned to the client',
                namespace='jina',
                labelnames=('runtime_name',),
                registry=metrics_registry,
            ).labels(runtime_name)

            self._sent_response_bytes = Summary(
                'sent_response_bytes',
                'The size in bytes of the request returned to the client',
                namespace='jina',
                labelnames=('runtime_name',),
                registry=metrics_registry,
            ).labels(runtime_name)

        else:
            self._receiving_request_metrics = None
            self._pending_requests_metrics = None
            self._failed_requests_metrics = None
            self._successful_requests_metrics = None
            self._request_size_metrics = None
            self._sent_response_bytes = None

        if meter:
            self._receiving_request_histogram = meter.create_histogram(
                name='jina_receiving_request_seconds',
                description='Time spent processing successful request',
            )

            self._pending_requests_up_down_counter = meter.create_up_down_counter(
                name='jina_number_of_pending_requests',
                description='Number of pending requests',
            )

            self._failed_requests_counter = meter.create_counter(
                name='jina_failed_requests',
                description='Number of failed requests',
            )

            self._successful_requests_counter = meter.create_counter(
                name='jina_successful_requests',
                description='Number of successful requests',
            )

            self._request_size_histogram = meter.create_histogram(
                name='jina_received_request_bytes',
                description='The size in bytes of the request returned to the client',
            )

            self._sent_response_bytes_histogram = meter.create_histogram(
                name='jina_sent_response_bytes',
                description='The size in bytes of the request returned to the client',
            )
        else:
            self._receiving_request_histogram = None
            self._pending_requests_up_down_counter = None
            self._failed_requests_counter = None
            self._successful_requests_counter = None
            self._request_size_histogram = None
            self._sent_response_bytes_histogram = None
        self._metric_labels = {'runtime_name': runtime_name}

    def _update_start_request_metrics(self, request: 'Request'):
        if self._request_size_metrics:
            self._request_size_metrics.observe(request.nbytes)
        if self._request_size_histogram:
            self._request_size_histogram.record(
                request.nbytes, attributes=self._metric_labels
            )

        if self._receiving_request_metrics:
            self._request_init_time[request.request_id] = time.time()
        if self._receiving_request_histogram:
            self._meter_request_init_time[request.request_id] = time.time()

        if self._pending_requests_metrics:
            self._pending_requests_metrics.inc()
        if self._pending_requests_up_down_counter:
            self._pending_requests_up_down_counter.add(
                1, attributes=self._metric_labels
            )

    def _update_end_successful_requests_metrics(self, result: 'Request'):
        if (
            self._receiving_request_metrics
        ):  # this one should only be observed when the metrics is succesful
            init_time = self._request_init_time.pop(
                result.request_id
            )  # need to pop otherwise it stays in memory forever
            self._receiving_request_metrics.observe(time.time() - init_time)
        if (
            self._receiving_request_histogram
        ):  # this one should only be observed when the metrics is succesful
            init_time = self._meter_request_init_time.pop(
                result.request_id
            )  # need to pop otherwise it stays in memory forever
            self._receiving_request_histogram.record(
                time.time() - init_time, attributes=self._metric_labels
            )

        if self._pending_requests_metrics:
            self._pending_requests_metrics.dec()
        if self._pending_requests_up_down_counter:
            self._pending_requests_up_down_counter.add(
                -1, attributes=self._metric_labels
            )

        if self._successful_requests_metrics:
            self._successful_requests_metrics.inc()
        if self._successful_requests_counter:
            self._successful_requests_counter.add(1, attributes=self._metric_labels)

        if self._sent_response_bytes:
            self._sent_response_bytes.observe(result.nbytes)
        if self._sent_response_bytes_histogram:
            self._sent_response_bytes_histogram.record(
                result.nbytes, attributes=self._metric_labels
            )

    def _update_end_failed_requests_metrics(self):
        if self._pending_requests_metrics:
            self._pending_requests_metrics.dec()
        if self._pending_requests_up_down_counter:
            self._pending_requests_up_down_counter.add(
                -1, attributes=self._metric_labels
            )

        if self._failed_requests_metrics:
            self._failed_requests_metrics.inc()
        if self._failed_requests_counter:
            self._failed_requests_counter.add(1, attributes=self._metric_labels)

    def _update_end_request_metrics(self, result: 'Request'):

        if result.status.code != jina_pb2.StatusProto.ERROR:
            self._update_end_successful_requests_metrics(result)
        else:
            self._update_end_failed_requests_metrics()


class RequestHandler(MonitoringRequestMixin):
    """
    Class that handles the requests arriving to the gateway and the result extracted from the requests future.

    :param metrics_registry: optional metrics registry for prometheus used if we need to expose metrics from the executor or from the data request handler
    :param runtime_name: optional runtime_name that will be registered during monitoring
    """

    def __init__(
        self,
        metrics_registry: Optional['CollectorRegistry'] = None,
        meter: Optional['Meter'] = None,
        runtime_name: Optional[str] = None,
    ):
        super().__init__(metrics_registry, meter, runtime_name)
        self._executor_endpoint_mapping = None
        self._gathering_endpoints = False

    def handle_request(
        self, graph: 'TopologyGraph', connection_pool: 'GrpcConnectionPool'
    ) -> Callable[['Request'], 'Tuple[Future, Optional[Future]]']:
        """
        Function that handles the requests arriving to the gateway. This will be passed to the streamer.

        :param graph: The TopologyGraph of the Flow.
        :param connection_pool: The connection pool to be used to send messages to specific nodes of the graph
        :return: Return a Function that given a Request will return a Future from where to extract the response
        """

        async def gather_endpoints(request_graph):
            nodes = request_graph.all_nodes
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

        def _handle_request(request: 'Request') -> 'Tuple[Future, Optional[Future]]':
            self._update_start_request_metrics(request)

            # important that the gateway needs to have an instance of the graph per request
            request_graph = copy.deepcopy(graph)

            if graph.has_filter_conditions:
                request_doc_ids = request.data.docs[
                    :, 'id'
                ]  # used to maintain order of docs that are filtered by executors
            responding_tasks = []
            floating_tasks = []
            endpoint = request.header.exec_endpoint
            r = request.routes.add()
            r.executor = 'gateway'
            r.start_time.GetCurrentTime()
            # If the request is targeting a specific deployment, we can send directly to the deployment instead of
            # querying the graph
            num_outgoing_nodes = len(request_graph.origin_nodes)
            has_specific_params = False
            request_input_parameters = request.parameters
            for key in request_input_parameters:
                if _is_param_for_specific_executor(key):
                    has_specific_params = True
                    break

            target_executor = request.header.target_executor
            # reset it in case we send to an external gateway
            request.header.target_executor = ''

            for origin_node in request_graph.origin_nodes:
                leaf_tasks = origin_node.get_leaf_tasks(
                    connection_pool=connection_pool,
                    request_to_send=request,
                    previous_task=None,
                    endpoint=endpoint,
                    executor_endpoint_mapping=self._executor_endpoint_mapping,
                    target_executor_pattern=target_executor or None,
                    request_input_parameters=request_input_parameters,
                    request_input_has_specific_params=has_specific_params,
                    copy_request_at_send=num_outgoing_nodes > 1 and has_specific_params,
                )
                # Every origin node returns a set of tasks that are the ones corresponding to the leafs of each of their
                # subtrees that unwrap all the previous tasks. It starts like a chain of waiting for tasks from previous
                # nodes
                responding_tasks.extend([task for ret, task in leaf_tasks if ret])
                floating_tasks.extend([task for ret, task in leaf_tasks if not ret])

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
                try:
                    if (
                        self._executor_endpoint_mapping is None
                        and not self._gathering_endpoints
                    ):
                        self._gathering_endpoints = True
                        asyncio.create_task(gather_endpoints(request_graph))

                    partial_responses = await asyncio.gather(*tasks)
                except Exception as e:
                    # update here failed request
                    self._update_end_failed_requests_metrics()
                    raise
                partial_responses, metadatas = zip(*partial_responses)
                filtered_partial_responses = list(
                    filter(lambda x: x is not None, partial_responses)
                )

                response = filtered_partial_responses[0]
                request_graph.add_routes(response)

                if graph.has_filter_conditions:
                    _sort_response_docs(response)

                collect_results = request_graph.collect_all_results()
                resp_params = response.parameters
                if len(collect_results) > 0:
                    resp_params[DataRequestHandler._KEY_RESULT] = collect_results
                    response.parameters = resp_params
                return response

            # In case of empty topologies
            if not responding_tasks:
                r.end_time.GetCurrentTime()
                future = asyncio.Future()
                future.set_result((request, {}))
                responding_tasks.append(future)

            return (
                asyncio.ensure_future(
                    _process_results_at_end_gateway(responding_tasks, request_graph)
                ),
                asyncio.ensure_future(asyncio.gather(*floating_tasks))
                if len(floating_tasks) > 0
                else None,
            )

        return _handle_request

    def handle_result(self) -> Callable[['Request'], 'Request']:
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

            self._update_end_request_metrics(result)

            return result

        return _handle_result
