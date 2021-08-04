import os
from typing import Union, Optional
import asyncio

from jina import __default_host__

from .....importer import ImportExtensions
from ...zmq.asyncio import AsyncNewLoopRuntime
from .app import get_fastapi_app

if False:
    import multiprocessing
    import threading

__all__ = ['HTTPRuntime']


class HTTPRuntime(AsyncNewLoopRuntime):
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

        from .....helper import extend_rest_interface

        self._server = UviServer(
            config=Config(
                app=extend_rest_interface(get_fastapi_app(self.args, self.logger)),
                host=__default_host__,
                port=self.args.port_expose,
                log_level=os.getenv('JINA_LOG_LEVEL', 'error').lower(),
            )
        )
        await self._server.setup()

    async def async_run_forever(self):
        """Running method of ther server."""
        await self._server.serve()

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        # handle terminate signals
        while not self.is_cancel.is_set() and not self._server.should_exit:
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def async_cancel(self):
        """Stop the server."""
        self._server.should_exit = True
        await self._server.shutdown()

    @staticmethod
    def wait_ready_or_shutdown(
        timeout: Optional[float],
        ready_or_shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        **kwargs
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ready_or_shutdown_event: the multiprocessing event to detect if the process failed or succeeded
        :param kwargs: extra keyword arguments

        :return: True if is ready or it needs to be shutdown
        """
        return ready_or_shutdown_event.wait(timeout)
