"""Module wrapping the Client of Jina."""
from .base import BaseClient, CallbackFnType, InputType, InputDeleteType
from .helper import callback_exec
from .mixin import PostMixin
from .request import GeneratorSourceType
from .websocket import WebSocketClientMixin


class Client(PostMixin, BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    @property
    def client(self) -> 'Client':
        """Return the client object itself

        .. # noqa: DAR201"""
        return self


class WebSocketClient(Client, WebSocketClientMixin):
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
