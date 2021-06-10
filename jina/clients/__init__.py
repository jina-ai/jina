"""Module wrapping the Client of Jina."""
import argparse
from typing import overload, Optional

from .base import BaseClient, CallbackFnType, InputType, InputDeleteType
from .helper import callback_exec
from .mixin import PostMixin
from .request import GeneratorSourceType
from .websocket import WebSocketClientMixin

__all__ = ['Client', 'GRPCClient', 'WebSocketClient']


# overload_inject_start_client
@overload
def Client(
    continue_on_error: Optional[bool] = False,
    host: Optional[str] = '0.0.0.0',
    port_expose: Optional[int] = None,
    proxy: Optional[bool] = False,
    request_size: Optional[int] = 100,
    restful: Optional[bool] = False,
    return_results: Optional[bool] = False,
    show_progress: Optional[bool] = False,
    **kwargs
) -> 'BaseClient':
    """Create a Client. Client is how user interact with Flow

    :param continue_on_error: If set, a Request that causes error will be logged only without blocking the further requests.
    :param host: The host address of the runtime, by default it is 0.0.0.0.
    :param port_expose: The port of the host exposed to the public
    :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
    :param request_size: The number of Documents in each Request.
    :param restful: If set, use RESTful interface instead of gRPC as the main interface
    :param return_results: This feature is only used for AsyncClient.

          If set, the results of all Requests will be returned as a list. This is useful when one wants
          process Responses in bulk instead of using callback.
    :param show_progress: If set, client will show a progress bar on receiving every request.
    :return: the new Client object

    .. # noqa: DAR202
    .. # noqa: DAR101
    .. # noqa: DAR003
    """
    # overload_inject_end_client


def Client(args: Optional['argparse.Namespace'] = None, **kwargs) -> 'BaseClient':
    """Jina Python client.

    :param args: Namespace args.
    :param kwargs: Additional arguments.
    :return: An instance of :class:`GRPCClient` or :class:`WebSocketClient`.
    """
    is_restful = kwargs.get('restful', False)
    if is_restful:
        return WebSocketClient(args, **kwargs)
    else:
        return GRPCClient(args, **kwargs)


class GRPCClient(PostMixin, BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    @property
    def client(self) -> 'GRPCClient':
        """Return the client object itself
        .. # noqa: DAR201"""
        return self


class WebSocketClient(GRPCClient, WebSocketClientMixin):
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
