from .base import InputFnType, BaseClient, CallbackFnType
from .websockets import WebSocketClientMixin
from ..enums import RequestType


class AsyncClient(BaseClient):
    """
    :class:`AsyncClient` is the asynchronous version of the :class:`Client`. They share the same interface, except
    in :class:`AsyncClient` :meth:`train`, :meth:`index`, :meth:`search` methods are coroutines
    (i.e. declared with the async/await syntax), simply calling them will not schedule them to be executed.
    To actually run a coroutine, user need to put them in an eventloop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncClient` can be very useful in
    the integration settings, where Jina/Flow/Client is NOT the main logic, but rather served as a part of other program.
    In this case, users often do not want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Client`
    is controlling and wrapping the eventloop internally, making the Client looks synchronous from outside.

    For example, say you have the Flow running in remote. You want to use Client to connect to it do
    some index and search, but meanwhile you have some other IO-bounded jobs and want to do them concurrently.
    You can use :class:`AsyncClient`,

    .. highlight:: python
    .. code-block:: python

        from jina.clients.asyncio import AsyncClient

        ac = AsyncClient(...)

        async def jina_client_query():
            await ac.search(...)

        async def heavylifting():
            await other_library.download_big_files(...)

        async def concurrent_main():
            await asyncio.gather(jina_client_query(), heavylifting())


        if __name__ == '__main__':
            # under python
            asyncio.run(concurrent_main())

    One can think of :class:`Client` as Jina-managed eventloop, whereas :class:`AsyncClient` is self-managed eventloop.
    """

    async def train(self, input_fn: InputFnType = None,
                    on_done: CallbackFnType = None,
                    on_error: CallbackFnType = None,
                    on_always: CallbackFnType = None,
                    **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.TRAIN
        return await self._get_results(input_fn, on_done, on_error, on_always, **kwargs)

    async def search(self, input_fn: InputFnType = None,
                     on_done: CallbackFnType = None,
                     on_error: CallbackFnType = None,
                     on_always: CallbackFnType = None,
                     **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.SEARCH
        return await self._get_results(input_fn, on_done, on_error, on_always, **kwargs)

    async def index(self, input_fn: InputFnType = None,
                    on_done: CallbackFnType = None,
                    on_error: CallbackFnType = None,
                    on_always: CallbackFnType = None,
                    **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.INDEX
        return await self._get_results(input_fn, on_done, on_error, on_always, **kwargs)


class AsyncWebSocketClient(AsyncClient, WebSocketClientMixin):
    """
    :class:`AsyncWebSocketClient` is the asynchronous version of the :class:`WebSocketClient`.
    They share the same interface, except in :class:`AsyncWebSocketClient` :meth:`train`, :meth:`index`, :meth:`search`
    methods are coroutines (i.e. declared with the async/await syntax), simply calling them will not schedule them to be executed.
    To actually run a coroutine, user need to put them in an eventloop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncWebSocketClient` can be very useful in the integration settings, where Jina/Flow/Client is NOT the
    main logic, but rather served as a part of other program. In this case, users often do not want to let Jina control
    the ``asyncio.eventloop``. On contrary, :class:`WebSocketClient` is controlling and wrapping the eventloop
    internally, making the Client looks synchronous from outside.

    For example, say you have the Flow running in remote. You want to use Client to connect to it do
    some index and search, but meanwhile you have some other IO-bounded jobs and want to do them concurrently.
    You can use :class:`AsyncWebSocketClient`,

    .. highlight:: python
    .. code-block:: python

        from jina.clients.asyncio import AsyncWebSocketClient

        ac = AsyncWebSocketClient(...)

        async def jina_client_query():
            await ac.search(...)

        async def heavylifting():
            await other_library.download_big_files(...)

        async def concurrent_main():
            await asyncio.gather(jina_client_query(), heavylifting())


        if __name__ == '__main__':
            # under python
            asyncio.run(concurrent_main())

    One can think of :class:`WebSocketClient` as Jina-managed eventloop,
    whereas :class:`AsyncWebSocketClient` is self-managed eventloop.
    """
