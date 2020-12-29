import asyncio
from multiprocessing.synchronize import Event

from ..grpc import GatewayPea
from .app import get_fastapi_app
from .....importer import ImportExtensions

__all__ = ['RESTGatewayPea']


class RESTGatewayPea(GatewayPea):

    async def serve_forever(self, is_ready_event: 'Event'):
        with ImportExtensions(required=True):
            from uvicorn import Config, Server

        class UvicornCustomServer(Server):
            def run(self, sockets=None):
                # uvicorn only supports predefined event loops
                # hence we implement a way to serve from a custom (already running) loop
                asyncio.create_task(self.serve(sockets=sockets))

        # change log_level for REST server debugging
        # TODO(Deepankar): The default `websockets` implementation needs the max_size to be set.
        # But uvicorn doesn't expose a config for max_size of a ws message, hence falling back to `ws='wsproto'`
        # Change to 'auto' once https://github.com/encode/uvicorn/pull/538 gets merged as 'wsproto' is less performant
        config = Config(app=get_fastapi_app(self.args, self.logger),
                        host=self.args.host,
                        port=self.args.port_expose,
                        ws='wsproto',
                        log_level='critical')
        self._server = UvicornCustomServer(config=config)
        self.logger.success(f'{self.__class__.__name__} is listening at: {self.args.host}:{self.args.port_expose}')
        self._server.run()
        is_ready_event.set()

    async def serve_terminate(self):
        await self._server.shutdown()
