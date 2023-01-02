import logging
import os
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from jina.importer import ImportExtensions
from jina.serve.gateway import BaseGateway

if TYPE_CHECKING:
    from fastapi import FastAPI


class FastAPIBaseGateway(BaseGateway):
    """Base FastAPI gateway. Implement this abstract class in-case you want to build a fastapi-based Gateway by
    implementing the `app` property. This property should return a fastapi app. The base Gateway will handle starting
    a server and serving the application using that server."""

    def __init__(
        self,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        uvicorn_kwargs: Optional[dict] = None,
        proxy: bool = False,
        **kwargs
    ):
        """Initialize the FastAPIBaseGateway
        :param ssl_keyfile: the path to the key file
        :param ssl_certfile: the path to the certificate file
        :param uvicorn_kwargs: Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server
        :param proxy: If set, respect the http_proxy and https_proxy environment variables, otherwise, it will unset
            these proxy variables before start. gRPC seems to prefer no proxy
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
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
        '''Get a FastAPI app'''
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
        self.server.should_exit = True
        await self.server.shutdown()

    async def run_server(self):
        """Run HTTP server forever"""
        await self.server.serve()


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
        from jina.serve.runtimes.gateway.http.models import JinaHealthModel

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
