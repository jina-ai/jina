"""Module wrapping AsyncIO ops for clients."""
from typing import Union, List

from .base import InputType, InputDeleteType, BaseClient, CallbackFnType
from .websocket import WebSocketClientMixin
from ..enums import RequestType
from ..helper import deprecated_alias


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

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    async def train(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs
    ) -> None:
        """Issue 'train' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :yield: result
        """
        self.mode = RequestType.TRAIN
        async for r in self._get_results(
            inputs, on_done, on_error, on_always, **kwargs
        ):
            yield r

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    async def search(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs
    ) -> None:
        """Issue 'search' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :yield: result
        """
        self.mode = RequestType.SEARCH
        self.add_default_kwargs(kwargs)
        async for r in self._get_results(
            inputs, on_done, on_error, on_always, **kwargs
        ):
            yield r

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    async def index(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs
    ) -> None:
        """Issue 'index' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :yield: result
        """
        self.mode = RequestType.INDEX
        async for r in self._get_results(
            inputs, on_done, on_error, on_always, **kwargs
        ):
            yield r

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    async def delete(
        self,
        inputs: InputDeleteType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs
    ) -> None:
        """Issue 'delete' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :yield: result
        """
        self.mode = RequestType.DELETE
        async for r in self._get_results(
            inputs, on_done, on_error, on_always, **kwargs
        ):
            yield r

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    async def update(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs
    ) -> None:
        """Issue 'update' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :yield: result
        """
        self.mode = RequestType.UPDATE
        async for r in self._get_results(
            inputs, on_done, on_error, on_always, **kwargs
        ):
            yield r

    async def reload(
        self,
        targets: Union[str, List[str]],
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs
    ):
        """Send 'reload' request to the Flow.

        :param targets: the regex string or list of regex strings to match the pea/pod names.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :yield: result
        """

        if isinstance(targets, str):
            targets = [targets]
        kwargs['targets'] = targets

        self.mode = RequestType.CONTROL
        async for r in self._get_results([], on_done, on_error, on_always, **kwargs):
            yield r


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
