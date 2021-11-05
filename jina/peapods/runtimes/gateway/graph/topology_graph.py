import asyncio

from collections import defaultdict
from typing import List, Optional, Dict


# pod6 -> needs: pod5, pod4
# pod5 -> needs: gateway
# pod4 -> needs: pod2, pod3
# pod2 -> needs: pod1
# pod3 -> needs: gateway
# pod1 -> needs: gateway


# gateway |-> pod1 -> pod2 -->
#         |                   | -> pod4 --->
#         |-> pod3 ---------->             | -> pod6
#         |-> pod5 ------------------------>


class TopologyGraph:
    class _ReqReplyNode:
        def __init__(
            self,
            name: str,
            number_of_parts=1,
        ):
            self.name = name
            self.outgoing_nodes = []
            self.number_of_parts = number_of_parts
            self.parts_to_send = []

        @property
        def leaf(self):
            return len(self.outgoing_nodes) == 0

        async def _wait_previous_and_send(
            self, msg, previous_task: Optional[asyncio.Task], connection_pool
        ):
            if previous_task is not None:
                msg = await previous_task
            if msg is not None:
                self.parts_to_send.append(msg)
                # this is a specific needs
                if len(self.parts_to_send) == self.number_of_parts:
                    resp = await connection_pool.send(self.parts_to_send[-1], self.name)
                    return resp

        def get_leaf_tasks(
            self,
            connection_pool,
            msg_to_send: Optional[str],
            previous_task: Optional[asyncio.Task],
        ) -> List[asyncio.Task]:
            """
            Gets all the tasks corresponding from all the subgraphs born from this node

            :param connection_pool: The connection_pool need to actually send the messages
            :param msg_to_send: Optional message to be sent when the node is an origin of a graph
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

            :return: Return a list of tasks corresponding to the leafs of all the subgraphs born from this node.
                These tasks will be based on awaiting for the task from previous_node and sending a message to the corresponding node.
            """
            wait_previous_and_send_task = asyncio.create_task(
                self._wait_previous_and_send(
                    msg_to_send, previous_task, connection_pool
                )
            )
            if self.leaf:  # I am like a leaf
                return [wait_previous_and_send_task]  # I am the last in the chain
            tasks = []
            for outgoing_node in self.outgoing_nodes:
                t = outgoing_node.get_leaf_tasks(
                    connection_pool, None, wait_previous_and_send_task
                )
                # We are interested in the last one, that will be the task that awaits all the previous
                tasks.append(t[-1])
            return tasks

    def __init__(self, graph_representation: Dict, *args, **kwargs):
        num_parts_per_node = defaultdict(int)
        node_names_in_outgoing = set()
        node_set = set()
        for node_name, outgoing_node_names in graph_representation.items():
            node_set.add(node_name)
            for out_node_name in outgoing_node_names:
                node_set.add(out_node_name)
                node_names_in_outgoing.add(out_node_name)
                num_parts_per_node[out_node_name] += 1

        nodes = {}
        for node_name in node_set:
            nodes[node_name] = self._ReqReplyNode(
                name=node_name,
                number_of_parts=num_parts_per_node[node_name]
                if num_parts_per_node[node_name] > 0
                else 1,
            )

        for node_name, outgoing_node_names in graph_representation.items():
            for out_node_name in outgoing_node_names:
                nodes[node_name].outgoing_nodes.append(nodes[out_node_name])

        origin_node_names = node_set.difference(node_names_in_outgoing)
        self._origin_nodes = [nodes[node_name] for node_name in origin_node_names]

    @property
    def origin_nodes(self):
        return self._origin_nodes
