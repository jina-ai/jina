import copy
import asyncio

from typing import List, Optional


class ConnectionPool:
    def __init__(self, *args, **kwargs):
        self.args = None

    async def wait_async(self, msg):
        await asyncio.sleep(0.01)
        req_id = msg[-1]
        return f'Response-{req_id}'

    async def send(self, msg, pod, head=True) -> str:
        return await self.wait_async(msg)


class Node:
    def __init__(self, pod_name, connection_pool, outgoing_nodes: List['Node']):
        self.pod_name = pod_name
        self.connection_pool = connection_pool
        self.outgoing_nodes = outgoing_nodes
        self.futures = []

    async def _send_message(self, msg):
        # ask connection pool to send to `self.pod_name`
        return await self.connection_pool.send(msg, self.pod_name)

    @property
    def last(self):
        return len(self.outgoing_nodes) == 0

    def send_and_forward(self, msg_to_send: Optional[str], previous_task: Optional[asyncio.Task]) -> asyncio.Task:
        async def _wait_previous_and_send(msg, t):
            if t is not None:
                msg = await t
            resp = await self._send_message(msg)
            resp = f'from {self.pod_name} ' + resp
            return resp

        wait_and_send_task = asyncio.create_task(_wait_previous_and_send(msg_to_send, previous_task))
        if self.last:
            return wait_and_send_task  # I am the last in the chain
        t = self.outgoing_nodes[0].send_and_forward(None, wait_and_send_task)
        return t


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


class Graph:
    def __init__(self, *args, **kwargs):
        self.connection_pool = ConnectionPool(*args, **kwargs)

    @staticmethod
    def build(*args, **kwargs):
        return Graph()

    @property
    def origin_nodes(self):
        return [
            Node(
                pod_name='pod0',
                connection_pool=self.connection_pool,
                outgoing_nodes=[
                    Node(
                        pod_name='pod1', connection_pool=self.connection_pool, outgoing_nodes=[
                            Node(
                                pod_name='pod2', connection_pool=self.connection_pool, outgoing_nodes=[]
                            )
                        ]
                    )
                ],
            )
        ]


class GatewayRuntime:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph = Graph(*args, **kwargs)

    async def receive_from_client(self, msg):
        graph = copy.deepcopy(self.graph)
        origin_node = graph.origin_nodes[0]
        t = origin_node.send_and_forward(msg, None)
        resp = await t
        return resp
        # merge responses and send back to client


if __name__ == '__main__':
    async def main():
        runtime = GatewayRuntime()
        resps = await asyncio.gather(runtime.receive_from_client('Request-1'), runtime.receive_from_client('Request-2'), runtime.receive_from_client('Request-3'))
        print(f' resps {resps}')

    asyncio.run(main())
