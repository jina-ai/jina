import asyncio

from collections import defaultdict
from typing import List, Optional, Dict, Tuple

from .....proto import jina_pb2
from ....networking import GrpcConnectionPool
from .....types.request.data import DataRequest


class TopologyGraph:
    """
    :class TopologyGraph is a class that describes a computational graph of nodes, where each node represents
        a Pod that needs to be sent requests in the order respecting the path traversal.

    :param graph_description: A dictionary describing the topology of the Pods. 2 special nodes are expected, the name `start-gateway` and `end-gateway` to
        determine the nodes that receive the very first request and the ones whose response needs to be sent back to the client. All the nodes with no outgoing nodes
        will be considered to be hanging, and they will be "flagged" so that the user can ignore their tasks and not await them.
    """

    class _ReqReplyNode:
        def __init__(self, name: str, number_of_parts: int = 1, hanging: bool = False):
            self.name = name
            self.outgoing_nodes = []
            self.number_of_parts = number_of_parts
            self.hanging = hanging
            self.parts_to_send = []

        @property
        def leaf(self):
            return len(self.outgoing_nodes) == 0

        async def _wait_previous_and_send(
            self,
            request: DataRequest,
            previous_task: Optional[asyncio.Task],
            connection_pool: GrpcConnectionPool,
        ):
            metadata = {}
            if previous_task is not None:
                result = await previous_task
                request, metadata = result[0], result[1]
            if 'is-error' in metadata:
                if request.routes and request.routes[-1].pod != 'gateway':
                    request.routes[-1].end_time.GetCurrentTime()
                    request.routes[-1].status.CopyFrom(request.header.status)
                return request, {}
            elif request is not None:
                self.parts_to_send.append(request)
                if request.routes and request.routes[-1].pod != 'gateway':
                    request.routes[-1].end_time.GetCurrentTime()
                # this is a specific needs
                if len(self.parts_to_send) == self.number_of_parts:
                    for request in self.parts_to_send:
                        r = request.routes.add()
                        r.pod = self.name
                        r.start_time.GetCurrentTime()
                    resp, metadata = await connection_pool.send_requests_once(
                        requests=self.parts_to_send, pod=self.name, head=True
                    )
                    for route in resp.response.routes:
                        if route.pod == self.name:
                            if resp.header.status.code == jina_pb2.StatusProto.ERROR:
                                route.status.CopyFrom(resp.header.status)
                            route.end_time.GetCurrentTime()
                            break
                    return resp, metadata
            return None, {}

        def get_leaf_tasks(
            self,
            connection_pool: GrpcConnectionPool,
            request_to_send: Optional[DataRequest],
            previous_task: Optional[asyncio.Task],
        ) -> List[Tuple[bool, asyncio.Task]]:
            """
            Gets all the tasks corresponding from all the subgraphs born from this node

            :param connection_pool: The connection_pool need to actually send the requests
            :param request_to_send: Optional request to be sent when the node is an origin of a graph
            :param previous_task: Optional task coming from the predecessor of the Node

            .. note:
                pod1 -> outgoing_nodes: pod2
                pod2 -> outgoing_nodes: pod4
                pod3 -> outgoing_nodes: pod4
                pod4 -> outgoing_nodes: pod6
                pod5 -> outgoing_nodes: pod6
                pod6 -> outgoing_nodes: []

                |-> pod1 -> pod2 -->
                |                   | -> pod4 --->
                |-> pod3 ---------->             | -> pod6
                |-> pod5 ------------------------>

                Let's imagine a graph from this. Node corresponding to Pod6 will receive 2 calls from pod4 and pod5.
                The task returned by `pod6` will backpropagated to the caller of pod1.get_leaf_tasks, pod3.get_leaf_tasks and pod5.get_leaf_tasks.

                When the caller of these methods await them, they will fire the logic of sending requests and responses from and to every pod

            :return: Return a list of tuples, where tasks corresponding to the leafs of all the subgraphs born from this node are in each tuple.
                These tasks will be based on awaiting for the task from previous_node and sending a request to the corresponding node. The other member of the pair
                is a flag indicating if the task is to be awaited by the gateway or not.
            """
            wait_previous_and_send_task = asyncio.create_task(
                self._wait_previous_and_send(
                    request_to_send, previous_task, connection_pool
                )
            )
            if self.leaf:  # I am like a leaf
                return [
                    (not self.hanging, wait_previous_and_send_task)
                ]  # I am the last in the chain
            hanging_tasks_tuples = []
            for outgoing_node in self.outgoing_nodes:
                t = outgoing_node.get_leaf_tasks(
                    connection_pool, None, wait_previous_and_send_task
                )
                # We are interested in the last one, that will be the task that awaits all the previous
                hanging_tasks_tuples.extend(t)

            return hanging_tasks_tuples

    def __init__(self, graph_representation: Dict, *args, **kwargs):
        num_parts_per_node = defaultdict(int)
        if 'start-gateway' in graph_representation:
            origin_node_names = graph_representation['start-gateway']
        else:
            origin_node_names = set()
        hanging_pod_names = set()
        node_set = set()
        for node_name, outgoing_node_names in graph_representation.items():
            if node_name not in {'start-gateway', 'end-gateway'}:
                node_set.add(node_name)
            if len(outgoing_node_names) == 0:
                hanging_pod_names.add(node_name)
            for out_node_name in outgoing_node_names:
                if out_node_name not in {'start-gateway', 'end-gateway'}:
                    node_set.add(out_node_name)
                    num_parts_per_node[out_node_name] += 1

        nodes = {}
        for node_name in node_set:
            nodes[node_name] = self._ReqReplyNode(
                name=node_name,
                number_of_parts=num_parts_per_node[node_name]
                if num_parts_per_node[node_name] > 0
                else 1,
                hanging=node_name in hanging_pod_names,
            )

        for node_name, outgoing_node_names in graph_representation.items():
            if node_name not in ['start-gateway', 'end-gateway']:
                for out_node_name in outgoing_node_names:
                    if out_node_name not in ['start-gateway', 'end-gateway']:
                        nodes[node_name].outgoing_nodes.append(nodes[out_node_name])

        self._origin_nodes = [nodes[node_name] for node_name in origin_node_names]

    @property
    def origin_nodes(self):
        """
        The list of origin nodes, the one that depend only on the gateway, so all the subgraphs will be born from them and they will
        send to their pods the request as received by the client.

        :return: A list of nodes
        """
        return self._origin_nodes
