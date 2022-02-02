import os
import asyncio

from jina import __default_host__

from jina.importer import ImportExtensions
from jina.serve.runtimes.gateway import GatewayRuntime

__all__ = ['HTTPGatewayRuntime']


class HTTPGatewayRuntime(GatewayRuntime):
    """Runtime for HTTP interface."""

    async def async_setup(self):
        """
        The async method setup the runtime.

        Setup the uvicorn server.
        """
        with ImportExtensions(required=True):
            from uvicorn import Config, Server

        class UviServer(Server):
            """The uvicorn server."""

            async def setup(self, sockets=None):
                """
                Setup uvicorn server.

                :param sockets: sockets of server.
                """
                config = self.config
                if not config.loaded:
                    config.load()
                self.lifespan = config.lifespan_class(config)
                self.install_signal_handlers()
                await self.startup(sockets=sockets)
                if self.should_exit:
                    return

            async def serve(self, **kwargs):
                """
                Start the server.

                :param kwargs: keyword arguments
                """
                await self.main_loop()

        uvicorn_kwargs = self.args.uvicorn_kwargs or {}
        self._set_topology_graph()
        self._set_connection_pool()
        from jina.serve.stream import RequestStreamer
        from jina.serve.runtimes.gateway.request_handling import (
            handle_request,
            handle_result,
        )

        streamer = RequestStreamer(
            args=self.args,
            request_handler=handle_request(
                graph=self._topology_graph, connection_pool=self._connection_pool
            ),
            result_handler=handle_result,
        )
        streamer.Call = streamer.stream

        uvi_app = None
        if self.args.uvicorn_app_path is None:
            from jina.serve.runtimes.gateway.http.app import get_uvicorn_app

            uvi_app = get_uvicorn_app(
                self.args,
                flow_fn=streamer.Call,
                close_fn=self._connection_pool.close,
                logger=self.logger,
            )
        else:
            from importlib import import_module

            mod = import_module(self.args.uvicorn_app_path)
            uvi_app = getattr(mod, 'get_uvicorn_app')(
                self.args,
                flow_fn=streamer.Call,
                close_fn=self._connection_pool.close,
                logger=self.logger,
            )

        # we check if there is a fastapi app provided by user. (how do we import it?) (they gave us an app.py) #
        # maybe we need to dynamically import get_uvicorn_app from this app.py
        self._server = UviServer(
            config=Config(
                app=uvi_app,
                host=__default_host__,
                port=self.args.port_expose,
                log_level=os.getenv('JINA_LOG_LEVEL', 'error').lower(),
                **uvicorn_kwargs
            )
        )
        await self._server.setup()

    async def async_run_forever(self):
        """Running method of ther server."""
        self._connection_pool.start()
        await self._server.serve()

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        # handle terminate signals
        while not self.is_cancel.is_set() and not self._server.should_exit:
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def async_teardown(self):
        """Shutdown the server."""
        await self._server.shutdown()
        await self._connection_pool.close()

    async def async_cancel(self):
        """Stop the server."""
        self._server.should_exit = True
