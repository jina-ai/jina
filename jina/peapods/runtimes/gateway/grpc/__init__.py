import os

import grpc

from jina import __default_host__

from .....proto import jina_pb2_grpc
from .. import GatewayRuntime
from ....stream.gateway import GatewayStreamer

__all__ = ['GRPCGatewayRuntime']


class GRPCGatewayRuntime(GatewayRuntime):
    """Gateway Runtime for gRPC."""

    async def async_setup(self):
        """
        The async method to setup.

        Create the gRPC server and expose the port for communication.
        """
        if not self.args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        self.server = grpc.aio.server(
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )
        self._set_topology_graph()
        self._set_connection_pool()

        self.streamer = GatewayStreamer(
            self.args, graph=self._topology_graph, connection_pool=self._connection_pool
        )

        jina_pb2_grpc.add_JinaRPCServicer_to_server(self.streamer, self.server)
        bind_addr = f'{__default_host__}:{self.args.port_expose}'
        self.server.add_insecure_port(bind_addr)
        self.logger.debug(f' Start server bound to {bind_addr}')
        await self.server.start()

    async def async_teardown(self):
        """Close the connection pool"""
        # usually async_cancel should already have been called, but then its a noop
        # if the runtime is stopped without a sigterm (e.g. as a context manager, this can happen)
        await self.async_cancel()
        self._connection_pool.close()

    async def async_cancel(self):
        """The async method to stop server."""
        await self.server.stop(0)

    async def async_run_forever(self):
        """The async running of server."""
        await self.server.wait_for_termination()
