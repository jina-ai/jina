"""Module wrapping the Client of Jina."""
import argparse
from typing import overload, Optional, Union, TYPE_CHECKING

__all__ = ['Client']

from jina.enums import GatewayProtocolType

if TYPE_CHECKING:
    from jina.clients.grpc import GRPCClient, AsyncGRPCClient
    from jina.clients.websocket import WebSocketClient, AsyncWebSocketClient
    from jina.clients.http import HTTPClient, AsyncHTTPClient


# overload_inject_start_client
@overload
def Client(
    *,
    asyncio: Optional[bool] = False,
    host: Optional[str] = '0.0.0.0',
    https: Optional[bool] = False,
    port: Optional[int] = None,
    protocol: Optional[str] = 'GRPC',
    proxy: Optional[bool] = False,
    return_responses: Optional[bool] = False,
    **kwargs
) -> Union[
    'AsyncWebSocketClient',
    'WebSocketClient',
    'AsyncGRPCClient',
    'GRPCClient',
    'HTTPClient',
    'AsyncHTTPClient',
]:
    """Create a Client. Client is how user interact with Flow

    :param asyncio: If set, then the input and output of this Client work in an asynchronous manner.
    :param host: The host address of the runtime, by default it is 0.0.0.0.
    :param https: If set, connect to gateway using https
    :param port: The port of the Gateway, which the client should connect to.
    :param protocol: Communication protocol between server and client.
    :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
    :param return_responses: If set, return results as List of Requests instead of a reduced DocArray.
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
    'AsyncGRPCClient',
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
            from jina.clients.grpc import AsyncGRPCClient

            return AsyncGRPCClient(args, **kwargs)
        else:
            from jina.clients.grpc import GRPCClient

            return GRPCClient(args, **kwargs)
    elif protocol == GatewayProtocolType.WEBSOCKET:
        if is_async:
            from jina.clients.websocket import AsyncWebSocketClient

            return AsyncWebSocketClient(args, **kwargs)
        else:
            from jina.clients.websocket import WebSocketClient

            return WebSocketClient(args, **kwargs)
    elif protocol == GatewayProtocolType.HTTP:
        if is_async:
            from jina.clients.http import AsyncHTTPClient

            return AsyncHTTPClient(args, **kwargs)
        else:
            from jina.clients.http import HTTPClient

            return HTTPClient(args, **kwargs)
