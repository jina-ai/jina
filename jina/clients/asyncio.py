"""Module wrapping AsyncIO ops for clients."""
from .base import BaseClient
from .mixin import AsyncPostMixin
from .websocket import WebSocketClientMixin


class AsyncClient(AsyncPostMixin, BaseClient):
    """
    :class:`AsyncClient` is the asynchronous version of the :class:`Client`.

    They share the same interface, except in :class:`AsyncClient` :meth:`train`, :meth:`index`,
    :meth:`search` methods are coroutines (i.e. declared with the async/await syntax),
    simply calling them will not schedule them to be executed.

    To actually run a coroutine, user need to put them in an event loop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncClient` can be very useful in
    the integration settings, where Jina/Flow/Client is NOT the main logic, but rather served as a part of other program.
    In this case, users often do not want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Client`
    is controlling and wrapping the event loop internally, making the Client looks synchronous from outside.

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
