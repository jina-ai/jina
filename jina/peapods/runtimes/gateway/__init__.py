from abc import ABC

from jina.peapods.runtimes.gateway.graph.topology_graph import TopologyGraph
from jina.peapods.networking import create_connection_pool

from jina.peapods.runtimes.asyncio import AsyncNewLoopRuntime


class GatewayRuntime(AsyncNewLoopRuntime, ABC):
    """
    The Runtime from which the GatewayRuntimes need to inherit
    """

    def _set_topology_graph(self):
        # check if it should be in K8s, maybe ConnectionPoolFactory to be created
        import json

        graph_description = json.loads(self.args.graph_description)
        self._topology_graph = TopologyGraph(graph_description)

    def _set_connection_pool(self):
        import json

        pods_addresses = json.loads(self.args.pods_addresses)
        # add the connections needed
        self._connection_pool = create_connection_pool(
            logger=self.logger,
            k8s_connection_pool=self.args.k8s_connection_pool,
            k8s_namespace=self.args.k8s_namespace,
        )
        for pod_name, addresses in pods_addresses.items():
            for address in addresses:
                self._connection_pool.add_connection(
                    pod=pod_name, address=address, head=True
                )
