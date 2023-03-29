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
        return await self._request_handler._load_balance(request)

    async def setup_server(self):
        """
        Initialize and return server
        """
        self.app = web.Application()
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)

    async def run_server(self):
        """Run HTTP server forever"""
        #await asyncio.sleep(3)
        await web._run_app(
            app=self.app,
            host=self.host,
            port=self.port,
        )
        # if we are here, it finished
        #self._server_exit = True

    async def shutdown(self):
        self._server_exit = True
        await super().shutdown()
        await self._request_handler.close()

    @property
    def _should_exit(self):
        return self._server_exit

    @property
    def should_exit(self):
        return self._should_exit
