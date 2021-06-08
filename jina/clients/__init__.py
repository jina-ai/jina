"""Module wrapping the Client of Jina."""
from .base import BaseClient, CallbackFnType, InputType, InputDeleteType
from .helper import callback_exec
from .mixin import PostMixin
from .request import GeneratorSourceType
from .websocket import WebSocketClientMixin
from ..parsers import set_client_cli_parser

__all__ = ['Client', 'GrpcClient', 'WebSocketClient']


def Client(host: str, port: int, restful: bool = False) -> 'BaseClient':
    """Jina Python client.

    :param host: Host address of the flow.
    :param port: Port number of the flow.
    :param restful: If connect to a Restful gateway, default is ``False``, connect to GrpcGateway.
    :return: An instance of :class:`GrpcClient` or :class:`WebSocketClient`.
    """
    args = set_client_cli_parser().parse_args(
        ['--host', host, '--port-expose', str(port)]
    )
    if restful:
        return WebSocketClient(args)
    else:
        return GrpcClient(args)


class GrpcClient(PostMixin, BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    @property
    def client(self) -> 'GrpcClient':
        """Return the client object itself
        .. # noqa: DAR201"""
        return self


class WebSocketClient(GrpcClient, WebSocketClientMixin):
    """A Python Client to stream requests from a Flow with a REST Gateway.

    :class:`WebSocketClient` shares the same interface as :class:`Client` and provides methods like
    :meth:`index`, "meth:`search`, :meth:`train`, :meth:`update` & :meth:`delete`.

    It is used by default while running operations when we create a `Flow` with `rest_api=True`

    .. highlight:: python
    .. code-block:: python

        from jina.flow import Flow
        f = Flow(rest_api=True).add().add()

        with f:
            f.index(['abc'])


    :class:`WebSocketClient` can also be used to run operations for a remote Flow

    .. highlight:: python
    .. code-block:: python

        # A Flow running on remote
        from jina.flow import Flow
        f = Flow(rest_api=True, port_expose=34567).add().add()

        with f:
            f.block()

        # Local WebSocketClient running index & search
        from jina.clients import WebSocketClient

        client = WebSocketClient(...)
        client.index(...)
        client.search(...)


    :class:`WebSocketClient` internally handles an event loop to run operations asynchronously.
    """
