from .app import get_fastapi_app
from ..base import AsyncZMQRuntime
from .....importer import ImportExtensions


__all__ = ['RESTRuntime']


class RESTRuntime(AsyncZMQRuntime):

    def setup(self):
        with ImportExtensions(required=True):
            from uvicorn import Config, Server

        # change log_level for REST server debugging
        # TODO(Deepankar): The default `websockets` implementation needs the max_size to be set.
        # But uvicorn doesn't expose a config for max_size of a ws message, hence falling back to `ws='wsproto'`
        # Change to 'auto' once https://github.com/encode/uvicorn/pull/538 gets merged,
        # as 'wsproto' is less performant and adds another dependency.
        self._server = Server(config=Config(app=get_fastapi_app(self.args, self.logger),
                                            host=self.args.host,
                                            port=self.args.port_expose,
                                            ws='wsproto',
                                            log_level='critical'))
        self.logger.success(f'{self.__class__.__name__} is listening at: {self.args.host}:{self.args.port_expose}')

    async def async_run_forever(self):
        await self._server.serve()

    async def async_cancel(self):
        self._server.should_exit = True
