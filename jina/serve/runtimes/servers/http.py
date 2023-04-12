import logging
import os
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from jina.importer import ImportExtensions
from jina.serve.runtimes.servers import BaseServer

if TYPE_CHECKING:
    from fastapi import FastAPI


class FastAPIBaseServer(BaseServer):
    """Base FastAPI server. Implement this abstract class in-case you want to build a fastapi-based server by
    implementing the `app` property. This property should return a fastapi app. The base Gateway will handle starting
    a server and serving the application using that server."""

    def __init__(
            self,
            ssl_keyfile: Optional[str] = None,
            ssl_certfile: Optional[str] = None,
            uvicorn_kwargs: Optional[dict] = None,
            proxy: bool = False,
            title: Optional[str] = None,
            description: Optional[str] = None,
            no_debug_endpoints: Optional[bool] = False,
            no_crud_endpoints: Optional[bool] = False,
            expose_endpoints: Optional[str] = None,
            expose_graphql_endpoint: Optional[bool] = False,
            cors: Optional[bool] = False,
            **kwargs
    ):
        """Initialize the FastAPIBaseGateway
        :param ssl_keyfile: the path to the key file
        :param ssl_certfile: the path to the certificate file
        :param uvicorn_kwargs: Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server
        :param proxy: If set, respect the http_proxy and https_proxy environment variables, otherwise, it will unset
            these proxy variables before start. gRPC seems to prefer no proxy
        :param title: The title of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param description: The description of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param no_debug_endpoints: If set, `/status` `/post` endpoints are removed from HTTP interface.
        :param no_crud_endpoints: If set, `/index`, `/search`, `/update`, `/delete` endpoints are removed from HTTP interface.
                  Any executor that has `@requests(on=...)` bound with those values will receive data requests.
        :param expose_endpoints: A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints.
        :param expose_graphql_endpoint: If set, /graphql endpoint is added to HTTP interface.
        :param cors: If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.no_debug_endpoints = no_debug_endpoints
        self.no_crud_endpoints = no_crud_endpoints
        self.expose_endpoints = expose_endpoints
        self.expose_graphql_endpoint = expose_graphql_endpoint
        self.cors = cors
        self.uvicorn_kwargs = uvicorn_kwargs or {}

        if ssl_keyfile and 'ssl_keyfile' not in self.uvicorn_kwargs.keys():
            self.uvicorn_kwargs['ssl_keyfile'] = ssl_keyfile

        if ssl_certfile and 'ssl_certfile' not in self.uvicorn_kwargs.keys():
            self.uvicorn_kwargs['ssl_certfile'] = ssl_certfile

        if not proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

    @property
    @abstractmethod
    def app(self):
        """Get a FastAPI app"""
        ...

    async def setup_server(self):
        """
        Initialize and return GRPC server
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

        # app property will generate a new fastapi app each time called
        app = self.app
        _install_health_check(app, self.logger)
        self.server = UviServer(
            config=Config(
                app=app,
                host=self.host,
                port=self.port,
                log_level=os.getenv('JINA_LOG_LEVEL', 'error').lower(),
                **self.uvicorn_kwargs,
            )
        )

        await self.server.setup()

    async def shutdown(self):
        """
        Free resources allocated when setting up HTTP server
        """
        await super().shutdown()
        self.server.should_exit = True
        await self.server.shutdown()

    async def run_server(self):
        """Run HTTP server forever"""
        await self.server.serve()

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

    @staticmethod
    def is_ready(ctrl_address: str, timeout: float = 1.0, **kwargs) -> bool:
        """
        Check if status is ready.
        :param ctrl_address: the address where the control request needs to be sent
        :param timeout: timeout of the health check in seconds
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        import urllib
        from http import HTTPStatus
        try:
            conn = urllib.request.urlopen(
                url=f'http://{ctrl_address}', timeout=timeout
            )
            return conn.code == HTTPStatus.OK
        except:
            return False

    @staticmethod
    async def async_is_ready(ctrl_address: str, timeout: float = 1.0, **kwargs) -> bool:
        """
        Async Check if status is ready.
        :param ctrl_address: the address where the control request needs to be sent
        :param timeout: timeout of the health check in seconds
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        return FastAPIBaseServer.is_ready(ctrl_address, timeout)


def _install_health_check(app: 'FastAPI', logger):
    health_check_exists = False
    for route in app.routes:
        if getattr(route, 'path', None) == '/' and 'GET' in getattr(
                route, 'methods', None
        ):
            health_check_exists = True
            logger.warning(
                'endpoint GET on "/" is used for health checks, make sure it\'s still accessible'
            )

    if not health_check_exists:
        from jina.serve.runtimes.gateway.models import JinaHealthModel

        @app.get(
            path='/',
            summary='Get the health of Jina Gateway service',
            response_model=JinaHealthModel,
        )
        async def _gateway_health():
            """
            Get the health of this Gateway service.
            .. # noqa: DAR201

            """
            return {}


class HTTPServer(FastAPIBaseServer):
    """
    :class:`HTTPServer` is a FastAPIBaseServer that uses the default FastAPI app for a given request handler
    """

    @property
    def app(self):
        """Get the default base API app for Server
        :return: Return a FastAPI app for the default HTTPGateway
        """
        return self._request_handler._http_fastapi_default_app(title=self.title,
                                                               description=self.description,
                                                               no_crud_endpoints=self.no_crud_endpoints,
                                                               no_debug_endpoints=self.no_debug_endpoints,
                                                               expose_endpoints=self.expose_endpoints,
                                                               expose_graphql_endpoint=self.expose_graphql_endpoint,
                                                               tracing=self.tracing,
                                                               tracer_provider=self.tracer_provider,
                                                               cors=self.cors)
