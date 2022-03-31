from abc import ABC

from jina.serve.networking import GrpcConnectionPool
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
        deployments_disable_reduce = json.loads(self.args.deployments_disable_reduce)
        self._topology_graph = TopologyGraph(
            graph_description, graph_conditions, deployments_disable_reduce
        )

    def _set_connection_pool(self):
        import json

        deployments_addresses = json.loads(self.args.deployments_addresses)
        # add the connections needed
        self._connection_pool = GrpcConnectionPool(
            logger=self.logger, compression=self.args.compression
        )
        for deployment_name, addresses in deployments_addresses.items():
            for address in addresses:
                self._connection_pool.add_connection(
                    deployment=deployment_name, address=address, head=True
                )
