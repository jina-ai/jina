from jina.clients.base.grpc import GRPCBaseClient
from jina.clients.mixin import AsyncPostMixin, HealthCheckMixin, PostMixin


class GRPCClient(GRPCBaseClient, PostMixin, HealthCheckMixin):
    """A client connecting to a Gateway using gRPC protocol."""


class AsyncGRPCClient(GRPCBaseClient, AsyncPostMixin, HealthCheckMixin):
    """
    Asynchronous client connecting to a Gateway using gRPC protocol.

    Unlike :class:`GRPCClient`, here :meth:`post` is a coroutine (i.e. declared with the async/await syntax),
    simply calling them will not schedule them to be executed.

    To actually run a coroutine, user need to put them in an event loop, e.g. via ``asyncio.run()``,
    ``asyncio.create_task()``.

    :class:`AsyncGRPCClient` can be very useful in
    the integration settings, where Jina/Flow/Client is NOT the main logic, but rather served as a part of other program.
    In this case, users often do **NOT** want to let Jina control the ``asyncio.eventloop``. On contrary, :class:`Client`
    is controlling and wrapping the event loop internally, making the Client looks synchronous from outside.

    """
