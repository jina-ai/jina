import logging
import os
from typing import Optional

from jina import __default_host__
from jina.helper import extend_rest_interface
from jina.importer import ImportExtensions

from ....gateway import BaseGateway
from . import get_fastapi_app


class WebSocketGateway(BaseGateway):
    """WebSocket Gateway implementation"""

    def __init__(
        self,
        port: Optional[int] = None,
        uvicorn_kwargs: Optional[dict] = None,
        **kwargs,
    ):
        """Initialize the gateway
        :param port: The port of the Gateway, which the client should connect to.
        :param uvicorn_kwargs: Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self.port = port
        self.uvicorn_kwargs = uvicorn_kwargs

    async def setup_server(self):
        """
        Setup WebSocket Server
        """
        self.app = extend_rest_interface(
            get_fastapi_app(
                streamer=self.streamer,
                logger=self.logger,
            )
        )

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

        uvicorn_kwargs = self.uvicorn_kwargs or {}

        for ssl_file in ['ssl_keyfile', 'ssl_certfile']:
            if ssl_file:
                if ssl_file not in uvicorn_kwargs.keys():
                    uvicorn_kwargs[ssl_file] = ssl_file

        self.server = UviServer(
            config=Config(
                app=self.app,
                host=__default_host__,
                port=self.port,
                ws_max_size=1024 * 1024 * 1024,
                log_level=os.getenv('JINA_LOG_LEVEL', 'error').lower(),
                **uvicorn_kwargs,
            )
        )

        await self.server.setup()

    async def teardown(self):
        """Free other resources allocated with the server, e.g, gateway object, ..."""
        await super().teardown()
        await self.server.shutdown()

    async def stop_server(self):
        """
        Stop WebSocket server
        """
        self.server.should_exit = True

    async def run_server(self):
        """Run WebSocket server forever"""
        await self.server.serve()

    @property
    def should_exit(self) -> bool:
        """
        Boolean flag that indicates whether the gateway server should exit or not
        :return: boolean flag
        """
        return self.server.should_exit
