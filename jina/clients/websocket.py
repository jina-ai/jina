from .base.websocket import WebSocketBaseClient
from .mixin import AsyncPostMixin, PostMixin


class WebSocketClient(WebSocketBaseClient, PostMixin):
    """
    A client communicates the server with WebSocket protocol.
    """


class AsyncWebSocketClient(WebSocketBaseClient, AsyncPostMixin):
    """
    A client communicates the server with WebSocket protocol.

    Unlike :class:`WebSocketClient`, here :meth:`post` is a coroutine (i.e. declared with the async/await syntax),
    simply calling them will not schedule them to be executed.

    To actually run a coroutine, user need to put them in an event loop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncWebSocketClient` can be very useful in
    the integration settings, where Jina/Flow/Client is NOT the main logic, but rather served as a part of other program.
    In this case, users often do not want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Client`
    is controlling and wrapping the event loop internally, making the Client looks synchronous from outside.

    """
