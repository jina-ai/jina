from abc import ABC

from jina.serve.networking import create_connection_pool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph


class GatewayRuntime(AsyncNewLoopRuntime, ABC):
    """
    The Runtime from which the GatewayRuntimes need to inherit
    """

    def _set_topology_graph(self):
        # check if it should be in K8s, maybe ConnectionPoolFactory to be created
        import json

        graph_description = json.loads(self.args.graph_description)
        graph_conditions = json.loads(self.args.graph_conditions)
        self._topology_graph = TopologyGraph(graph_description, graph_conditions)

    def _set_connection_pool(self):
        import json

        deployments_addresses = json.loads(self.args.deployments_addresses)
        # add the connections needed
        self._connection_pool = create_connection_pool(
            logger=self.logger,
            k8s_connection_pool=self.args.k8s_connection_pool,
            k8s_namespace=self.args.k8s_namespace,
            compression=self.args.compression,
        )
        for deployment_name, addresses in deployments_addresses.items():
            for address in addresses:
                self._connection_pool.add_connection(
                    deployment=deployment_name, address=address, head=True
                )
