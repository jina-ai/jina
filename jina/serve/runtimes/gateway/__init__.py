import argparse
from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph

if TYPE_CHECKING:
    import asyncio
    import multiprocessing
    import threading


class GatewayRuntime(AsyncNewLoopRuntime, ABC):
    """
    The Runtime from which the GatewayRuntimes need to inherit
    """

    def __init__(
        self,
        args: argparse.Namespace,
        cancel_event: Optional[
            Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
        ] = None,
        **kwargs,
    ):
        # this order is intentional: The timeout is needed in _set_topology_graph(), called by super
        self.timeout_send = args.timeout_send
        if self.timeout_send:
            self.timeout_send /= 1e3  # convert ms to seconds
        super().__init__(args, cancel_event, **kwargs)

    def _set_topology_graph(self):
        # check if it should be in K8s, maybe ConnectionPoolFactory to be created
        import json

        graph_description = json.loads(self.args.graph_description)
        graph_conditions = json.loads(self.args.graph_conditions)
        deployments_disable_reduce = json.loads(self.args.deployments_disable_reduce)
        self._topology_graph = TopologyGraph(
            graph_description,
            graph_conditions,
            deployments_disable_reduce,
            timeout_send=self.timeout_send,
            retries=self.args.retries,
        )

    def _set_connection_pool(self):
        import json

        deployments_addresses = json.loads(self.args.deployments_addresses)
        # add the connections needed
        self._connection_pool = GrpcConnectionPool(
            logger=self.logger,
            compression=self.args.compression,
            metrics_registry=self.metrics_registry,
        )
        for deployment_name, addresses in deployments_addresses.items():
            for address in addresses:
                self._connection_pool.add_connection(
                    deployment=deployment_name, address=address, head=True
                )
