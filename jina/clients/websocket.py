from jina.clients.base.websocket import WebSocketBaseClient
from jina.clients.mixin import (
    AsyncHealthCheckMixin,
    AsyncPostMixin,
    AsyncProfileMixin,
    HealthCheckMixin,
    PostMixin,
    ProfileMixin,
)


class WebSocketClient(WebSocketBaseClient, PostMixin, ProfileMixin, HealthCheckMixin):
    """A client connecting to a Gateway using WebSocket protocol.

    Instantiate this class through the :meth:`jina.Client` convenience method.

    EXAMPLE USAGE

    .. code-block:: python

        from jina import Client
        from docarray import Document

        # select host address to connect to
        c = Client(
            protocol='websocket', asyncio=False, host='ws://my.awesome.flow:1234'
        )  # returns WebSocketClient instance
        c.post(on='/index', inputs=Document(text='hello!'))

    """


class AsyncWebSocketClient(
    WebSocketBaseClient, AsyncPostMixin, AsyncProfileMixin, AsyncHealthCheckMixin
):
    """
    Asynchronous client connecting to a Gateway using WebSocket protocol.

    Instantiate this class through the :meth:`jina.Client` convenience method.

    Unlike :class:`WebSocketClient`, here :meth:`post` is a coroutine (i.e. declared with the async/await syntax),
    simply calling them will not schedule them to be executed.

    To actually run a coroutine, user need to put them in an event loop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncWebSocketClient` can be very useful in
    the integration settings, where Jina/Flow/Client is NOT the main logic, but rather served as a part of other program.
    In this case, users often do not want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Client`
    is controlling and wrapping the event loop internally, making the Client looks synchronous from outside.

    EXAMPLE USAGE

    .. code-block:: python

        from jina import Client
        from docarray import Document

        # async inputs for the client
        async def async_inputs():
            for _ in range(10):
                yield Document()
                await asyncio.sleep(0.1)


        # select host address to connect to
        c = Client(
            protocol='websocket', asyncio=True, host='http://ws.awesome.flow:1234'
        )  # returns AsyncWebSocketClient instance

        async for resp in client.post(on='/index', async_inputs, request_size=1):
            print(resp)

    """
