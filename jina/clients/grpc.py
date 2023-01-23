from jina.clients.base.grpc import GRPCBaseClient
from jina.clients.mixin import (
    AsyncHealthCheckMixin,
    AsyncPostMixin,
    HealthCheckMixin,
    PostMixin,
    ProfileMixin,
)


class GRPCClient(GRPCBaseClient, PostMixin, HealthCheckMixin, ProfileMixin):
    """A client connecting to a Gateway using gRPC protocol.

    Instantiate this class through the :meth:`jina.Client` convenience method.

    EXAMPLE USAGE

    .. code-block:: python

        from jina import Client
        from jina._docarray import Document

        # select host address to connect to
        c = Client(
            protocol='grpc', asyncio=False, host='grpc://my.awesome.flow:1234'
        )  # returns GRPCClient instance
        c.post(on='/index', inputs=Document(text='hello!'))

    """


class AsyncGRPCClient(GRPCBaseClient, AsyncPostMixin, AsyncHealthCheckMixin):
    """
    Asynchronous client connecting to a Gateway using gRPC protocol.

    Instantiate this class through the :meth:`jina.Client` convenience method.

    Unlike :class:`GRPCClient`, here :meth:`post` is a coroutine (i.e. declared with the async/await syntax),
    simply calling them will not schedule them to be executed.

    To actually run a coroutine, user need to put them in an event loop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncGRPCClient` can be very useful in
    the integration settings, where Jina/Flow/Client is NOT the main logic, but rather served as a part of other program.
    In this case, users often do **NOT** want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Client`
    is controlling and wrapping the event loop internally, making the Client looks synchronous from outside.

    EXAMPLE USAGE

    .. code-block:: python

        from jina import Client
        from jina._docarray import Document

        # async inputs for the client
        async def async_inputs():
            for _ in range(10):
                yield Document()
                await asyncio.sleep(0.1)


        # select host address to connect to
        c = Client(
            protocol='grpc', asyncio=True, host='grpc://my.awesome.flow:1234'
        )  # returns AsyncGRPCClient instance

        async for resp in client.post(on='/index', async_inputs, request_size=1):
            print(resp)

    """
