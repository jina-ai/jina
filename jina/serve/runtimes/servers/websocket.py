import logging
import os
from typing import Optional

from jina.importer import ImportExtensions
from jina.serve.runtimes.servers import BaseServer

from jina._docarray import docarray_v2


class WebSocketServer(BaseServer):
    """WebSocket Server implementation"""

    def __init__(
            self,
            ssl_keyfile: Optional[str] = None,
            ssl_certfile: Optional[str] = None,
            uvicorn_kwargs: Optional[dict] = None,
            proxy: Optional[bool] = None,
            **kwargs
    ):
        """Initialize the gateway
        :param ssl_keyfile: the path to the key file
        :param ssl_certfile: the path to the certificate file
        :param uvicorn_kwargs: Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server
        :param proxy: If set, respect the http_proxy and https_proxy environment variables, otherwise, it will unset
            these proxy variables before start. gRPC seems to prefer no proxy
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile
        self.uvicorn_kwargs = uvicorn_kwargs

        if not proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

    async def setup_server(self):
        """
        Setup WebSocket Server
        """
        self.logger.debug(f'Setting up Websocket server')
        if docarray_v2:
            from jina.serve.runtimes.gateway.request_handling import GatewayRequestHandler
            if isinstance(self._request_handler, GatewayRequestHandler):
                await self._request_handler.streamer._get_endpoints_input_output_models()
                self._request_handler.streamer._validate_flow_docarray_compatibility()
        self.app = self._request_handler._websocket_fastapi_default_app(tracing=self.tracing, tracer_provider=self.tracer_provider)

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

        if self.ssl_keyfile and 'ssl_keyfile' not in uvicorn_kwargs.keys():
            uvicorn_kwargs['ssl_keyfile'] = self.ssl_keyfile

        if self.ssl_certfile and 'ssl_certfile' not in uvicorn_kwargs.keys():
            uvicorn_kwargs['ssl_certfile'] = self.ssl_certfile

        self.server = UviServer(
            config=Config(
                app=self.app,
                host=self.host,
                port=self.port,
                ws_max_size=1024 * 1024 * 1024,
                log_level=os.getenv('JINA_LOG_LEVEL', 'error').lower(),
                **uvicorn_kwargs,
            )
        )
        self.logger.debug(f'UviServer server setup')
        await self.server.setup()
        self.logger.debug(f'Websocket server setup successful')

    @property
    def _should_exit(self):
        """Property describing if server is ready to exit
        :return: boolean indicating if Server ready to exit
        """
        return self.server.should_exit

    @property
    def should_exit(self):
        """Property describing if server is ready to exit
        :return: boolean indicating if Server ready to exit
        """
        return self._should_exit

    async def shutdown(self):
        """Free other resources allocated with the server, e.g, gateway object, ..."""
        self.logger.debug(f'Shutting down server')
        await super().shutdown()
        self.server.should_exit = True
        await self.server.shutdown()
        self.logger.debug(f'Server shutdown finished')

    async def run_server(self):
        """Run WebSocket server forever"""
        await self.server.serve()
