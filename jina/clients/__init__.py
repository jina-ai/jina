"""Module wrapping the Client of Jina."""
import argparse
from typing import overload, Optional, Union

__all__ = ['Client']

from ..enums import GatewayProtocolType

if False:
    from .base import BaseClient
    from .asyncio import AsyncClient, AsyncWebSocketClient, AsyncHTTPClient
    from .grpc import GRPCClient
    from .websocket import WebSocketClient
    from .http import HTTPClient


# overload_inject_start_client
@overload
def Client(
    asyncio: Optional[bool] = False,
    continue_on_error: Optional[bool] = False,
    host: Optional[str] = '0.0.0.0',
    port_expose: Optional[int] = None,
    protocol: Optional[str] = 'GRPC',
    proxy: Optional[bool] = False,
    request_size: Optional[int] = 100,
    return_results: Optional[bool] = False,
    show_progress: Optional[bool] = False,
    **kwargs
) -> Union[
    'AsyncWebSocketClient',
    'WebSocketClient',
    'AsyncClient',
    'GRPCClient',
    'HTTPClient',
    'AsyncHTTPClient',
]:
    """Create a Client. Client is how user interact with Flow

    :param asyncio: If set, then the input and output of this Client work in an asynchronous manner.
    :param continue_on_error: If set, a Request that causes error will be logged only without blocking the further requests.
    :param host: The host address of the runtime, by default it is 0.0.0.0.
    :param port_expose: The port of the host exposed to the public
    :param protocol: Communication protocol between server and client.
    :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
    :param request_size: The number of Documents in each Request.
    :param return_results: If set, the results of all Requests will be returned as a list. This is useful when one wants process Responses in bulk instead of using callback.
    :param show_progress: If set, client will show a progress bar on receiving every request.
    :return: the new Client object

    .. # noqa: DAR202
    .. # noqa: DAR101
    .. # noqa: DAR003
    """
    # overload_inject_end_client


def Client(
    args: Optional['argparse.Namespace'] = None, **kwargs
) -> Union[
    'AsyncWebSocketClient',
    'WebSocketClient',
    'AsyncClient',
    'GRPCClient',
    'HTTPClient',
    'AsyncHTTPClient',
]:
    """Jina Python client.

    :param args: Namespace args.
    :param kwargs: Additional arguments.
    :return: An instance of :class:`GRPCClient` or :class:`WebSocketClient`.
    """

    protocol = (
        args.protocol if args else kwargs.get('protocol', GatewayProtocolType.GRPC)
    )
    if isinstance(protocol, str):
        protocol = GatewayProtocolType.from_string(protocol)

    is_async = (args and args.asyncio) or kwargs.get('asyncio', False)

    if protocol == GatewayProtocolType.GRPC:
        if is_async:
            from .asyncio import AsyncClient

            return AsyncClient(args, **kwargs)
        else:
            from .grpc import GRPCClient

            return GRPCClient(args, **kwargs)
    elif protocol == GatewayProtocolType.WEBSOCKET:
        if is_async:
            from .asyncio import AsyncWebSocketClient

            return AsyncWebSocketClient(args, **kwargs)
        else:
            from .websocket import WebSocketClient

            return WebSocketClient(args, **kwargs)
    elif protocol == GatewayProtocolType.HTTP:
        if is_async:
            from .asyncio import AsyncHTTPClient

            return AsyncHTTPClient(args, **kwargs)
        else:
            from .http import HTTPClient

            return HTTPClient(args, **kwargs)
