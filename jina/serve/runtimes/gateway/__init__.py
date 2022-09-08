import argparse
from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime

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
        # this order is intentional: The timeout is needed in _create_topology_graph(), called by super
        self.timeout_send = args.timeout_send
        if self.timeout_send:
            self.timeout_send /= 1e3  # convert ms to seconds
        super().__init__(args, cancel_event, **kwargs)
        self._set_streamer()

    def _set_streamer(self):
        import json

        from jina.serve.streamer import GatewayStreamer

        graph_description = json.loads(self.args.graph_description)
        graph_conditions = json.loads(self.args.graph_conditions)
        deployments_addresses = json.loads(self.args.deployments_addresses)
        deployments_disable_reduce = json.loads(self.args.deployments_disable_reduce)

        self.streamer = GatewayStreamer(
            graph_representation=graph_description,
            executor_addresses=deployments_addresses,
            graph_conditions=graph_conditions,
            deployments_disable_reduce=deployments_disable_reduce,
            timeout_send=self.timeout_send,
            retries=self.args.retries,
            compression=self.args.compression,
            runtime_name=self.args.name,
            prefetch=self.args.prefetch,
            logger=self.logger,
            metrics_registry=self.metrics_registry,
        )
