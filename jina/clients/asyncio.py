"""Module wrapping AsyncIO ops for clients."""
from functools import partialmethod
from typing import Optional, Dict

from .base import InputType, BaseClient, CallbackFnType
from .websocket import WebSocketClientMixin
from .. import Response
from ..enums import RequestType


class AsyncClient(BaseClient):
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

    async def post(
            self,
            on: str,
            inputs: InputType,
            on_done: CallbackFnType = None,
            on_error: CallbackFnType = None,
            on_always: CallbackFnType = None,
            parameters: Optional[Dict] = None,
            target_peapod: Optional[str] = None,
            **kwargs,
    ) -> Optional[Response]:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_peapod: a regex string represent the certain peas/pods request targeted
        :param kwargs: additional parameters
        :return: None
        """
        self.mode = RequestType.DATA
        async for r in self._get_results(
                inputs=inputs,
                on_done=on_done,
                on_error=on_error,
                on_always=on_always,
                exec_endpoint=on,
                target_peapod=target_peapod,
                parameters=parameters,
                **kwargs,
        ):
            yield r

    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')


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
