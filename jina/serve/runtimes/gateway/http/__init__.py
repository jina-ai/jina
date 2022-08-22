import asyncio
import logging
import os

from jina import __default_host__
from jina.importer import ImportExtensions
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.gateway.http.app import get_fastapi_app

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

        if 'CICD_JINA_DISABLE_HEALTHCHECK_LOGS' in os.environ:

            class _EndpointFilter(logging.Filter):
                def filter(self, record: logging.LogRecord) -> bool:
                    # NOTE: space is important after `GET /`, else all logs will be disabled.
                    return record.getMessage().find("GET / ") == -1

            # Filter out healthcheck endpoint `GET /`
            logging.getLogger("uvicorn.access").addFilter(_EndpointFilter())

        from jina.helper import extend_rest_interface

        uvicorn_kwargs = self.args.uvicorn_kwargs or {}

        for ssl_file in ['ssl_keyfile', 'ssl_certfile']:
            if getattr(self.args, ssl_file):
                if ssl_file not in uvicorn_kwargs.keys():
                    uvicorn_kwargs[ssl_file] = getattr(self.args, ssl_file)

        self._server = UviServer(
            config=Config(
                app=extend_rest_interface(
                    get_fastapi_app(
                        args=self.args,
                        logger=self.logger,
                        timeout_send=self.timeout_send,
                        metrics_registry=self.metrics_registry,
                    )
                ),
                host=__default_host__,
                port=self.args.port,
                log_level=os.getenv('JINA_LOG_LEVEL', 'error').lower(),
                **uvicorn_kwargs
            )
        )
        await self._server.setup()

    async def async_run_forever(self):
        """Running method of the server."""
        await self._server.serve()

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPod`"""
        # handle terminate signals
        while not self.is_cancel.is_set() and not self._server.should_exit:
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def async_teardown(self):
        """Shutdown the server."""
        await self._server.shutdown()

    async def async_cancel(self):
        """Stop the server."""
        self._server.should_exit = True
