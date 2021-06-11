"""Module wrapping the Client of Jina."""
import argparse
from typing import overload, Optional, Union

__all__ = ['Client']

if False:
    from .base import BaseClient
    from .asyncio import AsyncClient, AsyncWebSocketClient
    from .grpc import GRPCClient
    from .websocket import WebSocketClient


# overload_inject_start_client
@overload
def Client(
    asyncio: Optional[bool] = False,
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

    :param asyncio: If set, then the input and output of this Client work in an asynchronous manner.
    :param continue_on_error: If set, a Request that causes error will be logged only without blocking the further requests.
    :param host: The host address of the runtime, by default it is 0.0.0.0.
    :param port_expose: The port of the host exposed to the public
    :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
    :param request_size: The number of Documents in each Request.
    :param restful: If set, use RESTful interface instead of gRPC as the main interface. This expects the corresponding Flow to be set with --restful as well.
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


def Client(
    args: Optional['argparse.Namespace'] = None, **kwargs
) -> Union['AsyncWebSocketClient', 'WebSocketClient', 'AsyncClient', 'GRPCClient']:
    """Jina Python client.

    :param args: Namespace args.
    :param kwargs: Additional arguments.
    :return: An instance of :class:`GRPCClient` or :class:`WebSocketClient`.
    """
    is_restful = (args and args.restful) or kwargs.get('restful', False)
    is_async = (args and args.asyncio) or kwargs.get('asyncio', False)

    if is_restful:
        if is_async:
            from .asyncio import AsyncWebSocketClient

            return AsyncWebSocketClient(args, **kwargs)
        else:
            from .websocket import WebSocketClient

            return WebSocketClient(args, **kwargs)
    else:
        if is_async:
            from .asyncio import AsyncClient

            return AsyncClient(args, **kwargs)
        else:
            from .grpc import GRPCClient

            return GRPCClient(args, **kwargs)
