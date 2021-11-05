import copy
import asyncio

from collections import defaultdict
from typing import List, Optional, Dict


class DummyMockConnectionPool:
    def __init__(self, *args, **kwargs):
        self.args = None

    async def wait_async(self, msg):
        import random

        await asyncio.sleep(1 / (random.randint(1, 3) * 10))
        req_id = msg[-1]
        return f'Response-{req_id}'

    async def send(self, msg, pod, head=True) -> str:
        return await self.wait_async(msg)


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
            node_name: str,
            number_of_parts=1,
        ):
            self.node_name = node_name
            self.outgoing_nodes = []
            self.number_of_parts = number_of_parts
            self.parts_to_send = []

        @property
        def last(self):
            return len(self.outgoing_nodes) == 0

        def send_and_forward(
            self,
            connection_pool,
            msg_to_send: Optional[str],
            previous_task: Optional[asyncio.Task],
            previous_pod: Optional[str] = None,
        ) -> List[asyncio.Task]:
            async def _wait_previous_and_send(msg, t):
                if t is not None:
                    msg = await t
                    print(f' {self.node_name} await from {previous_pod} => {msg}')
                if msg is not None:
                    self.parts_to_send.append(msg)
                    # this is a specific needs
                    if len(self.parts_to_send) == self.number_of_parts:
                        resp = await connection_pool.send(
                            self.parts_to_send[-1], self.node_name
                        )
                        resp = f'from {self.node_name} ' + resp
                        return resp
                else:
                    return f'waiting for other parts in {self.node_name}'

            wait_and_send_task = asyncio.create_task(
                _wait_previous_and_send(msg_to_send, previous_task)
            )
            if self.last:  # I am like a leaf
                return [wait_and_send_task]  # I am the last in the chain
            tasks = []
            for outgoing_node in self.outgoing_nodes:
                t = outgoing_node.send_and_forward(
                    connection_pool, None, wait_and_send_task, self.node_name
                )
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
                node_name=node_name,
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


class DummyMockGatewayRuntime:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_pool = DummyMockConnectionPool(*args, **kwargs)
        self.graph = TopologyGraph(*args, **kwargs)

    async def receive_from_client(self, msg):
        graph = copy.deepcopy(self.graph)
        tasks = []
        for origin_node in graph.origin_nodes:
            ts = origin_node.send_and_forward(self.connection_pool, msg, None)
            tasks.extend(ts)
        resp = await asyncio.gather(*tasks)
        return resp
        # merge responses and send back to client


if __name__ == '__main__':

    async def main():
        runtime = DummyMockGatewayRuntime()
        resps = await asyncio.gather(
            runtime.receive_from_client('Request-1'),
            runtime.receive_from_client('Request-2'),
            runtime.receive_from_client('Request-3'),
        )
        print(f' resps {resps}')

    asyncio.run(main())
