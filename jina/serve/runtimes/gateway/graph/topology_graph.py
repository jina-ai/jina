import asyncio
import copy
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import grpc.aio

from jina import __default_endpoint__
from jina.excepts import InternalNetworkError
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.helper import _parse_specific_params
from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler
from jina.types.request.data import DataRequest
from jina.logging.logger import JinaLogger


class TopologyGraph:
    """
    :class TopologyGraph is a class that describes a computational graph of nodes, where each node represents
        a Deployment that needs to be sent requests in the order respecting the path traversal.

    :param graph_description: A dictionary describing the topology of the Deployments. 2 special nodes are expected, the name `start-gateway` and `end-gateway` to
        determine the nodes that receive the very first request and the ones whose response needs to be sent back to the client. All the nodes with no outgoing nodes
        will be considered to be floating, and they will be "flagged" so that the user can ignore their tasks and not await them.

    :param conditions: A dictionary describing which Executors have special conditions to be fullfilled by the `Documents` to be sent to them.
    :param reduce: Reduce requests arriving from multiple needed predecessors, True by default
    """

    class _ReqReplyNode:
        def __init__(
            self,
            name: str,
            number_of_parts: int = 1,
            floating: bool = False,
            filter_condition: dict = None,
            metadata: Optional[Dict] = None,
            reduce: bool = True,
            timeout_send: Optional[float] = None,
            retries: Optional[int] = -1,
            logger: Optional[JinaLogger] = None,
        ):
            self.name = name
            self.outgoing_nodes = []
            self.number_of_parts = number_of_parts
            self.floating = floating
            self.parts_to_send = []
            self.start_time = None
            self.end_time = None
            self.status = None
            self._filter_condition = filter_condition
            self._metadata = metadata
            self._reduce = reduce
            self._timeout_send = timeout_send
            self._retries = retries
            self.result_in_params_returned = None
            self.logger = logger or JinaLogger(self.__class__.__name__)

        @property
        def leaf(self):
            return len(self.outgoing_nodes) == 0

        def _update_requests_with_filter_condition(self, need_copy):
            for i in range(len(self.parts_to_send)):
                req = (
                    self.parts_to_send[i]
                    if not need_copy
                    else copy.deepcopy(self.parts_to_send[i])
                )
                filtered_docs = req.docs.find(self._filter_condition)
                req.data.docs = filtered_docs
                self.parts_to_send[i] = req

        def _update_request_by_params(
            self, deployment_name: str, request_input_parameters: Dict
        ):
            specific_parameters = _parse_specific_params(
                request_input_parameters, deployment_name
            )
            for i in range(len(self.parts_to_send)):
                self.parts_to_send[i].parameters = specific_parameters

        def _handle_internalnetworkerror(self, err):
            err_code = err.code()
            if err_code == grpc.StatusCode.UNAVAILABLE:
                err._details = (
                    err.details()
                    + f' |Gateway: Communication error with deployment {self.name} at address(es) {err.dest_addr}. '
                    f'Head or worker(s) may be down.'
                )
                raise err
            elif err_code == grpc.StatusCode.DEADLINE_EXCEEDED:
                err._details = (
                    err.details()
                    + f'|Gateway: Connection with deployment {self.name} at address(es) {err.dest_addr} could be established, but timed out.'
                    f' You can increase the allowed time by setting `timeout_send` in your Flow YAML `with` block or Flow `__init__()` method.'
                )
                raise err
            else:
                raise

        def get_endpoints(self, connection_pool: GrpcConnectionPool) -> asyncio.Task:
            return connection_pool.send_discover_endpoint(
                self.name, retries=self._retries
            )

        async def _wait_previous_and_send(
            self,
            request: Optional[DataRequest],
            previous_task: Optional[asyncio.Task],
            connection_pool: GrpcConnectionPool,
            endpoint: Optional[str],
            executor_endpoint_mapping: Optional[Dict] = None,
            target_executor_pattern: Optional[str] = None,
            request_input_parameters: Dict = {},
            copy_request_at_send: bool = False,
        ):
            # Check my condition and send request with the condition
            metadata = {}
            if previous_task is not None:
                result = await previous_task
                request, metadata = result[0], result[1]
            if metadata and 'is-error' in metadata:
                return request, metadata
            elif request is not None:
                request.parameters = _parse_specific_params(
                    request.parameters, self.name
                )
                req_to_send = (
                    copy.deepcopy(request) if copy_request_at_send else request
                )
                self.parts_to_send.append(req_to_send)
                # this is a specific needs
                if len(self.parts_to_send) == self.number_of_parts:
                    self.start_time = datetime.utcnow()
                    self._update_request_by_params(self.name, request_input_parameters)
                    if self._filter_condition is not None:
                        self._update_requests_with_filter_condition(
                            need_copy=not copy_request_at_send
                        )
                    if self._reduce and len(self.parts_to_send) > 1:
                        self.parts_to_send = [
                            WorkerRequestHandler.reduce_requests(self.parts_to_send)
                        ]

                    # avoid sending to executor which does not bind to this endpoint
                    if endpoint is not None and executor_endpoint_mapping is not None:
                        if (self.name in executor_endpoint_mapping and
                            endpoint not in executor_endpoint_mapping[self.name]
                            and __default_endpoint__
                            not in executor_endpoint_mapping[self.name]
                        ):
                            return request, metadata

                    if target_executor_pattern is not None and not re.match(
                        target_executor_pattern, self.name
                    ):
                        return request, metadata
                    # otherwise, send to executor and get response
                    try:
                        print(f' send to {self.name} endpoint {endpoint}=> {len(self.parts_to_send[0].docs)}')
                        result = await connection_pool.send_requests_once(
                            requests=self.parts_to_send,
                            deployment=self.name,
                            metadata=self._metadata,
                            head=True,
                            endpoint=endpoint,
                            timeout=self._timeout_send,
                            retries=self._retries,
                        )
                        if issubclass(type(result), BaseException):
                            raise result
                        else:
                            resp, metadata = result

                        print(f' got from {self.name} => {len(resp.docs)}')
                        if WorkerRequestHandler._KEY_RESULT in resp.parameters:
                            # Accumulate results from each Node and then add them to the original
                            self.result_in_params_returned = resp.parameters[
                                WorkerRequestHandler._KEY_RESULT
                            ]
                        request.parameters = request_input_parameters
                        resp.parameters = request_input_parameters
                        print(f' CLEAR PARTS TO SEND')
                        self.parts_to_send.clear()
                    except InternalNetworkError as err:
                        self._handle_internalnetworkerror(err)
                    except Exception as err:
                        self.logger.error(f'Exception sending requests to {self.name}: {err}')
                        raise err

                    self.end_time = datetime.utcnow()
                    if metadata and 'is-error' in metadata:
                        self.status = resp.header.status
                    return resp, metadata

            return None, {}

        def get_leaf_tasks(
            self,
            connection_pool: GrpcConnectionPool,
            request_to_send: Optional[DataRequest],
            previous_task: Optional[asyncio.Task],
            endpoint: Optional[str] = None,
            executor_endpoint_mapping: Optional[Dict] = None,
            target_executor_pattern: Optional[str] = None,
            request_input_parameters: Dict = {},
            request_input_has_specific_params: bool = False,
            copy_request_at_send: bool = False,
        ) -> List[Tuple[bool, asyncio.Task]]:
            """
            Gets all the tasks corresponding from all the subgraphs born from this node

            :param connection_pool: The connection_pool need to actually send the requests
            :param request_to_send: Optional request to be sent when the node is an origin of a graph
            :param previous_task: Optional task coming from the predecessor of the Node
            :param endpoint: Optional string defining the endpoint of this request
            :param executor_endpoint_mapping: Optional map that maps the name of a Deployment with the endpoints that it binds to so that they can be skipped if needed
            :param target_executor_pattern: Optional regex pattern for the target executor to decide whether or not the Executor should receive the request
            :param request_input_parameters: The parameters coming from the Request as they arrive to the gateway
            :param request_input_has_specific_params: Parameter added for optimization. If this is False, there is no need to copy at all the request
            :param copy_request_at_send: Copy the request before actually calling the `ConnectionPool` sending

            .. note:
                deployment1 -> outgoing_nodes: deployment2
                deployment2 -> outgoing_nodes: deployment4
                deployment3 -> outgoing_nodes: deployment4
                deployment4 -> outgoing_nodes: deployment6
                deployment5 -> outgoing_nodes: deployment6
                deployment6 -> outgoing_nodes: []

                |-> deployment1 -> deployment2 -->
                |                   | -> deployment4 --->
                |-> deployment3 ---------->             | -> deployment6
                |-> deployment5 ------------------------>

                Let's imagine a graph from this. Node corresponding to Deployment6 will receive 2 calls from deployment4 and deployment5.
                The task returned by `deployment6` will backpropagated to the caller of deployment1.get_leaf_tasks, deployment3.get_leaf_tasks and deployment5.get_leaf_tasks.

                When the caller of these methods await them, they will fire the logic of sending requests and responses from and to every deployment

            :return: Return a list of tuples, where tasks corresponding to the leafs of all the subgraphs born from this node are in each tuple.
                These tasks will be based on awaiting for the task from previous_node and sending a request to the corresponding node. The other member of the pair
                is a flag indicating if the task is to be awaited by the gateway or not.
            """
            wait_previous_and_send_task = asyncio.create_task(
                self._wait_previous_and_send(
                    request=request_to_send,
                    previous_task=previous_task,
                    connection_pool=connection_pool,
                    endpoint=endpoint,
                    executor_endpoint_mapping=executor_endpoint_mapping,
                    target_executor_pattern=target_executor_pattern,
                    request_input_parameters=request_input_parameters,
                    copy_request_at_send=copy_request_at_send,
                )
            )
            if self.leaf:  # I am like a leaf
                return [
                    (not self.floating, wait_previous_and_send_task)
                ]  # I am the last in the chain
            hanging_tasks_tuples = []
            num_outgoing_nodes = len(self.outgoing_nodes)
            for outgoing_node in self.outgoing_nodes:
                t = outgoing_node.get_leaf_tasks(
                    connection_pool=connection_pool,
                    request_to_send=None,
                    previous_task=wait_previous_and_send_task,
                    endpoint=endpoint,
                    executor_endpoint_mapping=executor_endpoint_mapping,
                    target_executor_pattern=target_executor_pattern,
                    request_input_parameters=request_input_parameters,
                    request_input_has_specific_params=request_input_has_specific_params,
                    copy_request_at_send=num_outgoing_nodes > 1
                    and request_input_has_specific_params,
                )
                # We are interested in the last one, that will be the task that awaits all the previous
                hanging_tasks_tuples.extend(t)

            return hanging_tasks_tuples

        def add_route(self, request: 'DataRequest'):
            """
             Add routes to the DataRequest based on the state of request processing

             :param request: the request to add the routes to
            :return: modified request with added routes
            """

            def _find_route(request):
                for r in request.routes:
                    if r.executor == self.name:
                        return r
                return None

            r = _find_route(request)
            if r is None and self.start_time:
                r = request.routes.add()
                r.executor = self.name
                r.start_time.FromDatetime(self.start_time)
                if self.end_time:
                    r.end_time.FromDatetime(self.end_time)
                if self.status:
                    r.status.CopyFrom(self.status)
            for outgoing_node in self.outgoing_nodes:
                request = outgoing_node.add_route(request=request)
            return request

    class _EndGatewayNode(_ReqReplyNode):

        """
        Dummy node to be added before the gateway. This is to solve a problem we had when implementing `floating Executors`.
        If we do not add this at the end, this structure does not work:

            GATEWAY -> EXEC1 -> FLOATING
                    -> GATEWAY
        """

        def get_endpoints(self, *args, **kwargs) -> asyncio.Task:
            async def task_wrapper():
                from jina.serve.networking import default_endpoints_proto

                return default_endpoints_proto, None

            return asyncio.create_task(task_wrapper())

        def get_leaf_tasks(
            self, previous_task: Optional[asyncio.Task], *args, **kwargs
        ) -> List[Tuple[bool, asyncio.Task]]:
            return [(True, previous_task)]

    def __init__(
        self,
        graph_representation: Dict,
        graph_conditions: Dict = {},
        deployments_metadata: Dict = {},
        deployments_no_reduce: List[str] = [],
        timeout_send: Optional[float] = 1.0,
        retries: Optional[int] = -1,
        logger: Optional[JinaLogger] = None,
        *args,
        **kwargs,
    ):
        self.logger = logger or JinaLogger(self.__class__.__name__)
        num_parts_per_node = defaultdict(int)
        if 'start-gateway' in graph_representation:
            origin_node_names = graph_representation['start-gateway']
        else:
            origin_node_names = set()
        floating_deployment_set = set()
        node_set = set()
        for node_name, outgoing_node_names in graph_representation.items():
            if node_name not in {'start-gateway', 'end-gateway'}:
                node_set.add(node_name)
            if len(outgoing_node_names) == 0:
                floating_deployment_set.add(node_name)
            for out_node_name in outgoing_node_names:
                if out_node_name not in {'start-gateway', 'end-gateway'}:
                    node_set.add(out_node_name)
                    num_parts_per_node[out_node_name] += 1

        nodes = {}
        for node_name in node_set:
            condition = graph_conditions.get(node_name, None)
            metadata = deployments_metadata.get(node_name, None)
            nodes[node_name] = self._ReqReplyNode(
                name=node_name,
                number_of_parts=num_parts_per_node[node_name]
                if num_parts_per_node[node_name] > 0
                else 1,
                floating=node_name in floating_deployment_set,
                filter_condition=condition,
                metadata=metadata,
                reduce=node_name not in deployments_no_reduce,
                timeout_send=timeout_send,
                retries=retries,
                logger=self.logger
            )

        for node_name, outgoing_node_names in graph_representation.items():
            if node_name not in ['start-gateway', 'end-gateway']:
                for out_node_name in outgoing_node_names:
                    if out_node_name not in ['start-gateway', 'end-gateway']:
                        nodes[node_name].outgoing_nodes.append(nodes[out_node_name])
                    if out_node_name == 'end-gateway':
                        nodes[node_name].outgoing_nodes.append(
                            self._EndGatewayNode(name='__end_gateway__', floating=False)
                        )

        self._origin_nodes = [nodes[node_name] for node_name in origin_node_names]
        self.has_filter_conditions = bool(graph_conditions)

    def add_routes(self, request: 'DataRequest'):
        """
        Add routes to the DataRequest based on the state of request processing

        :param request: the request to add the routes to
        :return: modified request with added routes
        """
        for node in self._origin_nodes:
            request = node.add_route(request=request)
        return request

    @property
    def origin_nodes(self):
        """
        The list of origin nodes, the one that depend only on the gateway, so all the subgraphs will be born from them and they will
        send to their deployments the request as received by the client.

        :return: A list of nodes
        """
        return self._origin_nodes

    @property
    def all_nodes(self):
        """
        The set of all the nodes inside this Graph

        :return: A list of nodes
        """

        def _get_all_nodes(node, accum, accum_names):
            if node.name not in accum_names:
                accum.append(node)
                accum_names.append(node.name)
            for n in node.outgoing_nodes:
                _get_all_nodes(n, accum, accum_names)
            return accum, accum_names

        nodes = []
        node_names = []
        for origin_node in self.origin_nodes:
            subtree_nodes, subtree_node_names = _get_all_nodes(origin_node, [], [])
            for st_node, st_node_name in zip(subtree_nodes, subtree_node_names):
                if st_node_name not in node_names:
                    nodes.append(st_node)
                    node_names.append(st_node_name)
        return nodes

    def collect_all_results(self):
        """Collect all the results from every node into a single dictionary so that gateway can collect them

        :return: A dictionary of the results
        """
        res = {}
        for node in self.all_nodes:
            if node.result_in_params_returned:
                res.update(node.result_in_params_returned)
        return res
