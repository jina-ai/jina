from .app import get_fastapi_app
from ..base import AsyncNewLoopRuntime
from .....importer import ImportExtensions

__all__ = ['RESTRuntime']


class RESTRuntime(AsyncNewLoopRuntime):
    """Runtime for REST."""

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

            async def serve(self, sockets=None):
                """
                Start the server.

                :param sockets: sockets of server.
                """
                await self.main_loop()
                await self.shutdown(sockets=sockets)

        # change log_level for REST server debugging
        # TODO(Deepankar): The default `websockets` implementation needs the max_size to be set.
        # But uvicorn doesn't expose a config for max_size of a ws message, hence falling back to `ws='wsproto'`
        # Change to 'auto' once https://github.com/encode/uvicorn/pull/538 gets merged,
        # as 'wsproto' is less performant and adds another dependency.
        self._server = UviServer(
            config=Config(
                app=get_fastapi_app(self.args, self.logger),
                host=self.args.host,
                port=self.args.port_expose,
                ws='wsproto',
                log_level='critical',
            )
        )
        await self._server.setup()
        self.logger.success(
            f'{self.__class__.__name__} is listening at: {self.args.host}:{self.args.port_expose}'
        )

    async def async_run_forever(self):
        """Running method of ther server."""
        await self._server.serve()

    async def async_cancel(self):
        """Stop the server."""
        self._server.should_exit = True
