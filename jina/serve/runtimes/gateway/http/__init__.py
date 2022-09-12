import asyncio
import os

from jina import __default_host__
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.gateway.http.app import get_fastapi_app

__all__ = ['HTTPGatewayRuntime']

from jina.serve.runtimes.gateway.http.gateway import HTTPGateway


class HTTPGatewayRuntime(GatewayRuntime):
    """Runtime for HTTP interface."""

    async def async_setup(self):
        """
        The async method setup the runtime.

        Setup the uvicorn server.
        """
        self.gateway = HTTPGateway(
            self.args.port,
            self.args.title,
            self.args.description,
            self.args.no_debug_endpoints,
            self.args.no_crud_endpoints,
            self.args.expose_endpoints,
            self.args.expose_graphql_endpoints,
            self.args.cors,
            self.args.uvicorn_kwargs,
        )

        self.gateway._set_streamer(self.args, self.timeout_send, self.metrics_registry)
        await self.gateway.setup_server()

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPod`"""
        # handle terminate signals
        while not self.is_cancel.is_set() and not self.gateway.should_exit:
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def async_teardown(self):
        """Shutdown the server."""
        await self.gateway.teardown()

    async def async_cancel(self):
        """Stop the server."""
        await self.gateway.stop_server()

    async def async_run_forever(self):
        """Running method of the server."""
        await self.gateway.run_server()
