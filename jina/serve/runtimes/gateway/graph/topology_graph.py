import asyncio
import copy
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.request_handlers.data_request_handler import DataRequestHandler
from jina.types.request.data import DataRequest


class TopologyGraph:
    """
    :class TopologyGraph is a class that describes a computational graph of nodes, where each node represents
        a Deployment that needs to be sent requests in the order respecting the path traversal.

    :param graph_description: A dictionary describing the topology of the Deployments. 2 special nodes are expected, the name `start-gateway` and `end-gateway` to
        determine the nodes that receive the very first request and the ones whose response needs to be sent back to the client. All the nodes with no outgoing nodes
        will be considered to be hanging, and they will be "flagged" so that the user can ignore their tasks and not await them.

    :param conditions: A dictionary describing which Executors have special conditions to be fullfilled by the `Documents` to be sent to them.
    :param reduce: Reduce requests arriving from multiple needed predecessors, True by default
    """

    class _ReqReplyNode:
        def __init__(
            self,
            name: str,
            number_of_parts: int = 1,
            hanging: bool = False,
            filter_condition: dict = None,
            reduce: bool = True,
        ):
            self.name = name
            self.outgoing_nodes = []
            self.number_of_parts = number_of_parts
            self.hanging = hanging
            self.parts_to_send = []
            self.start_time = None
            self.end_time = None
            self.status = None
            self._filter_condition = filter_condition
            self._reduce = reduce

        @property
        def leaf(self):
            return len(self.outgoing_nodes) == 0

        def _update_requests(self):
            for i in range(len(self.parts_to_send)):
                copy_req = copy.deepcopy(self.parts_to_send[i])
                filtered_docs = copy_req.docs.find(self._filter_condition)
                copy_req.data.docs = filtered_docs
                self.parts_to_send[i] = copy_req

        async def _wait_previous_and_send(
            self,
            request: DataRequest,
            previous_task: Optional[asyncio.Task],
            connection_pool: GrpcConnectionPool,
            endpoint: Optional[str],
        ):
            # Check my condition and send request with the condition
            metadata = {}
            if previous_task is not None:
                result = await previous_task
                request, metadata = result[0], result[1]
            if 'is-error' in metadata:
                return request, metadata
            elif request is not None:
                self.parts_to_send.append(request)
                # this is a specific needs
                if len(self.parts_to_send) == self.number_of_parts:
                    self.start_time = datetime.utcnow()
                    if self._filter_condition is not None:
                        self._update_requests()
                    if self._reduce and len(self.parts_to_send) > 1:
                        self.parts_to_send = [
                            DataRequestHandler.reduce_requests(self.parts_to_send)
                        ]

                    resp, metadata = await connection_pool.send_requests_once(
                        requests=self.parts_to_send,
                        deployment=self.name,
                        head=True,
                        endpoint=endpoint,
                    )
                    self.end_time = datetime.utcnow()
                    if 'is-error' in metadata:
                        self.status = resp.header.status
                    return resp, metadata

            return None, {}

        def get_leaf_tasks(
            self,
            connection_pool: GrpcConnectionPool,
            request_to_send: Optional[DataRequest],
            previous_task: Optional[asyncio.Task],
            endpoint: Optional[str] = None,
        ) -> List[Tuple[bool, asyncio.Task]]:
            """
            Gets all the tasks corresponding from all the subgraphs born from this node

            :param connection_pool: The connection_pool need to actually send the requests
            :param request_to_send: Optional request to be sent when the node is an origin of a graph
            :param previous_task: Optional task coming from the predecessor of the Node
            :param endpoint: Optional string defining the endpoint of this request

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
                    request_to_send, previous_task, connection_pool, endpoint=endpoint
                )
            )
            if self.leaf:  # I am like a leaf
                return [
                    (not self.hanging, wait_previous_and_send_task)
                ]  # I am the last in the chain
            hanging_tasks_tuples = []
            for outgoing_node in self.outgoing_nodes:
                t = outgoing_node.get_leaf_tasks(
                    connection_pool,
                    None,
                    wait_previous_and_send_task,
                    endpoint=endpoint,
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

    def __init__(
        self,
        graph_representation: Dict,
        graph_conditions: Dict = {},
        deployments_disable_reduce: List[str] = [],
        *args,
        **kwargs
    ):
        num_parts_per_node = defaultdict(int)
        if 'start-gateway' in graph_representation:
            origin_node_names = graph_representation['start-gateway']
        else:
            origin_node_names = set()
        hanging_deployment_names = set()
        node_set = set()
        for node_name, outgoing_node_names in graph_representation.items():
            if node_name not in {'start-gateway', 'end-gateway'}:
                node_set.add(node_name)
            if len(outgoing_node_names) == 0:
                hanging_deployment_names.add(node_name)
            for out_node_name in outgoing_node_names:
                if out_node_name not in {'start-gateway', 'end-gateway'}:
                    node_set.add(out_node_name)
                    num_parts_per_node[out_node_name] += 1

        nodes = {}
        for node_name in node_set:
            condition = graph_conditions.get(node_name, None)
            nodes[node_name] = self._ReqReplyNode(
                name=node_name,
                number_of_parts=num_parts_per_node[node_name]
                if num_parts_per_node[node_name] > 0
                else 1,
                hanging=node_name in hanging_deployment_names,
                filter_condition=condition,
                reduce=node_name not in deployments_disable_reduce,
            )

        for node_name, outgoing_node_names in graph_representation.items():
            if node_name not in ['start-gateway', 'end-gateway']:
                for out_node_name in outgoing_node_names:
                    if out_node_name not in ['start-gateway', 'end-gateway']:
                        nodes[node_name].outgoing_nodes.append(nodes[out_node_name])

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
