from jina.clients.base.grpc import GRPCBaseClient
from jina.clients.mixin import AsyncPostMixin, PostMixin


class GRPCClient(GRPCBaseClient, PostMixin):
    """A client communicates the server with GRPC protocol."""


class AsyncGRPCClient(GRPCBaseClient, AsyncPostMixin):
    """
    A client communicates the server with GRPC protocol.

    Unlike :class:`GRPCClient`, here :meth:`post` is a coroutine (i.e. declared with the async/await syntax),
    simply calling them will not schedule them to be executed.

    To actually run a coroutine, user need to put them in an event loop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncGRPCClient` can be very useful in
    the integration settings, where Jina/Flow/Client is NOT the main logic, but rather served as a part of other program.
    In this case, users often do **NOT** want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Client`
    is controlling and wrapping the event loop internally, making the Client looks synchronous from outside.

    """
