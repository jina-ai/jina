from jina.serve.runtimes.servers import BaseServer
from aiohttp import web


class LoadBalancingServer(BaseServer):
    """Base FastAPI server. Implement this abstract class in-case you want to build a fastapi-based server by
    implementing the `app` property. This property should return a fastapi app. The base Gateway will handle starting
    a server and serving the application using that server."""

    def __init__(
            self,
            **kwargs
    ):
        """Initialize the LoadBalancingServer
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        # get server list from args
        self._server_exit = False

    async def handle_request(self, request):
        """Method called to handle requests coming to the LoadBalancer
        :param request: request to handle
        :return: the response to the request
        """
        return await self._request_handler._load_balance(request)

    async def setup_server(self):
        """
        Initialize and return server
        """
        self.logger.debug(f'Setting up LoadBalancer server')
        self.app = web.Application()
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
        self.logger.debug(f'LoadBalancer server setup successful')

    async def run_server(self):
        """Run HTTP server forever"""
        await web._run_app(
            app=self.app,
            host=self.host,
            port=self.port,
        )

    async def shutdown(self):
        """Shutdown the server and free other allocated resources, e.g, streamer object, health check service, ..."""
        self.logger.debug(f'Shutting down server')
        self._server_exit = True
        await super().shutdown()
        await self._request_handler.close()
        self.logger.debug(f'Server shutdown finished')

    @property
    def _should_exit(self):
        """Property describing if server is ready to exit
        :return: boolean indicating if Server ready to exit
        """
        return self._server_exit

    @property
    def should_exit(self):
        """Property describing if server is ready to exit
        :return: boolean indicating if Server ready to exit
        """
        return self._should_exit
