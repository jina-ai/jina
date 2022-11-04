import logging
import os
from typing import Optional

from jina import __default_host__
from jina.importer import ImportExtensions
from jina.serve.gateway import BaseGateway
from jina.serve.runtimes.gateway.http.app import get_fastapi_app


class HTTPGateway(BaseGateway):
    """HTTP Gateway implementation"""

    def __init__(
        self,
        port: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        no_debug_endpoints: Optional[bool] = False,
        no_crud_endpoints: Optional[bool] = False,
        expose_endpoints: Optional[str] = None,
        expose_graphql_endpoint: Optional[bool] = False,
        cors: Optional[bool] = False,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        uvicorn_kwargs: Optional[dict] = None,
        proxy: Optional[bool] = None,
        **kwargs
    ):
        """Initialize the gateway
            Get the app from FastAPI as the REST interface.
        :param port: The port of the Gateway, which the client should connect to.
        :param title: The title of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param description: The description of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param no_debug_endpoints: If set, `/status` `/post` endpoints are removed from HTTP interface.
        :param no_crud_endpoints: If set, `/index`, `/search`, `/update`, `/delete` endpoints are removed from HTTP interface.

                  Any executor that has `@requests(on=...)` bound with those values will receive data requests.
        :param expose_endpoints: A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints.
        :param expose_graphql_endpoint: If set, /graphql endpoint is added to HTTP interface.
        :param cors: If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
        :param ssl_keyfile: the path to the key file
        :param ssl_certfile: the path to the certificate file
        :param uvicorn_kwargs: Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server
        :param proxy: If set, respect the http_proxy and https_proxy environment variables, otherwise, it will unset
            these proxy variables before start. gRPC seems to prefer no proxy
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self.port = port
        self.title = title
        self.description = description
        self.no_debug_endpoints = no_debug_endpoints
        self.no_crud_endpoints = no_crud_endpoints
        self.expose_endpoints = expose_endpoints
        self.expose_graphql_endpoint = expose_graphql_endpoint
        self.cors = cors
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile
        self.uvicorn_kwargs = uvicorn_kwargs

        if not proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

    async def setup_server(self):
        """
        Initialize and return GRPC server
        """
        from jina.helper import extend_rest_interface

        self.app = extend_rest_interface(
            get_fastapi_app(
                streamer=self.streamer,
                title=self.title,
                description=self.description,
                no_debug_endpoints=self.no_debug_endpoints,
                no_crud_endpoints=self.no_crud_endpoints,
                expose_endpoints=self.expose_endpoints,
                expose_graphql_endpoint=self.expose_graphql_endpoint,
                cors=self.cors,
                logger=self.logger,
                tracing=self.tracing,
                tracer_provider=self.tracer_provider,
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

        if self.ssl_keyfile and 'ssl_keyfile' not in uvicorn_kwargs.keys():
            uvicorn_kwargs['ssl_keyfile'] = self.ssl_keyfile

        if self.ssl_certfile and 'ssl_certfile' not in uvicorn_kwargs.keys():
            uvicorn_kwargs['ssl_certfile'] = self.ssl_certfile

        self.server = UviServer(
            config=Config(
                app=self.app,
                host=__default_host__,
                port=self.port,
                log_level=os.getenv('JINA_LOG_LEVEL', 'error').lower(),
                **uvicorn_kwargs,
            )
        )

        await self.server.setup()

    async def teardown(self):
        """
        Free resources allocated when setting up HTTP server
        """
        await super().teardown()
        await self.server.shutdown()

    async def stop_server(self):
        """
        Stop HTTP server
        """
        self.server.should_exit = True

    async def run_server(self):
        """Run HTTP server forever"""
        await self.server.serve()

    @property
    def should_exit(self) -> bool:
        """
        Boolean flag that indicates whether the gateway server should exit or not
        :return: boolean flag
        """
        return self.server.should_exit
