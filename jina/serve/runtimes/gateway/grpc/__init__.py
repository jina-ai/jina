import os

from jina import __default_host__
from jina.excepts import PortAlreadyUsed
from jina.helper import is_port_free
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.gateway.grpc.gateway import GRPCGateway

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

        if not (is_port_free(__default_host__, self.args.port)):
            raise PortAlreadyUsed(f'port:{self.args.port}')

        self.gateway = GRPCGateway(
            name=self.name,
            grpc_server_options=self.args.grpc_server_options,
            port=self.args.port,
            ssl_keyfile=self.args.ssl_keyfile,
            ssl_certfile=self.args.ssl_certfile,
        )

        self.gateway.set_streamer(
            args=self.args,
            timeout_send=self.timeout_send,
            metrics_registry=self.metrics_registry,
            runtime_name=self.name,
        )
        await self.gateway.setup_server()

    async def async_teardown(self):
        """Close the connection pool"""
        # usually async_cancel should already have been called, but then its a noop
        # if the runtime is stopped without a sigterm (e.g. as a context manager, this can happen)
        await self.gateway.teardown()
        await self.async_cancel()

    async def async_cancel(self):
        """The async method to stop server."""
        await self.gateway.stop_server()

    async def async_run_forever(self):
        """The async running of server."""
        await self.gateway.run_server()
