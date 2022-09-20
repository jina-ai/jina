import asyncio

from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.gateway.websocket.app import get_fastapi_app

__all__ = ['WebSocketGatewayRuntime']

from jina.serve.runtimes.gateway.websocket.gateway import WebSocketGateway


class WebSocketGatewayRuntime(GatewayRuntime):
    """Runtime for Websocket interface."""

    async def async_setup(self):
        """
        The async method setup the runtime.

        Setup the uvicorn server.
        """

        self.gateway = WebSocketGateway(
            name=self.name,
            port=self.args.port,
            ssl_keyfile=self.args.ssl_keyfile,
            ssl_certfile=self.args.ssl_certfile,
            uvicorn_kwargs=self.args.uvicorn_kwargs,
            logger=self.logger,
        )

        self.gateway.set_streamer(
            args=self.args,
            timeout_send=self.timeout_send,
            metrics_registry=self.metrics_registry,
            runtime_name=self.args.name,
        )
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
        """Running method of ther server."""
        await self.gateway.run_server()
