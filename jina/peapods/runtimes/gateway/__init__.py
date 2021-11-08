from .graph.topology_graph import TopologyGraph
from ...networking import create_connection_pool

from ..zmq.asyncio import AsyncNewLoopRuntime


class GatewayRuntime(AsyncNewLoopRuntime):
    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self._set_topology_graph()
        self._set_connection_pool()

    def _set_topology_graph(self):
        # check if it should be in K8s, maybe ConnectionPoolFactory to be created
        import json

        graph_description = json.loads(self.args.graph_description)
        self._topology_graph = TopologyGraph(graph_description)

    def _set_connection_pool(self):
        # check if it should be in K8s
        import json

        pods_addresses = json.loads(self.args.pods_addresses)
        # add the connections needed
        self._connection_pool = create_connection_pool()
        for pod_name, addresses in pods_addresses:
            for address in addresses:
                self._connection_pool.add_connection(
                    pod=pod_name, address=address, head=True
                )
