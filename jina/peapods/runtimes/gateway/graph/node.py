import copy
import asyncio

from typing import List


class ConnectionPool:
    def __init__(self, *args, **kwargs):
        self.args = None

    async def wait_async(self):
        return 'Response'

    def send_message(self, msg, pod, head=True) -> List[asyncio.Task]:
        task = asyncio.create_task(self.wait_async())
        return [task]


class Node:

    def __init__(self, pod_name, connection_pool, needs: List['Node']):
        self.pod_name = pod_name
        self.connection_pool = connection_pool
        self.needs = needs
        self.futures = []

    def send_message(self, msg):
        # ask connection pool to send to `self.pod_name`
        task = self.connection_pool.send(msg, self.pod_name)[0]
        return task

    def _merge_responses(self, responses):
        return 'Response'

    @property
    def origin(self):
        return self.needs == ['GATEWAY']

    def get_response(self, msg):
        if self.origin:  # I receive the first message
            return self.send_message(msg)
        else:
            tasks = []
            for need in self.needs:
                tasks.append(need.get_response(msg))

            # wait for the tasks?
            responses = asyncio.gather(*tasks)
            # merge responses
            msg_to_send = self._merge_responses(responses)
            return self.send_message(msg_to_send)


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
    def end_nodes(self):
        return [Node(pod_name='pod2', connection_pool=self.connection_pool,
                     needs=[Node(pod_name='pod1', connection_pool=self.connection_pool, needs=[])])]


class GatewayRuntime:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph = Graph(*args, **kwargs)

    async def receive_from_client(self, msg):
        graph = copy.deepcopy(self.graph)
        tasks = []
        for end_node in graph.end_nodes:
            tasks.append(end_node.get_response(msg))

        responses = asyncio.gather(*tasks)
        # merge responses and send back to client
