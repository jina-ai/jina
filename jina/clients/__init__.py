"""Module wrapping the Client of Jina."""
import argparse
from typing import TYPE_CHECKING, Optional, Union, overload

from jina.helper import parse_client

__all__ = ['Client']

from jina.enums import GatewayProtocolType

if TYPE_CHECKING:
    from jina.clients.grpc import AsyncGRPCClient, GRPCClient
    from jina.clients.http import AsyncHTTPClient, HTTPClient
    from jina.clients.websocket import AsyncWebSocketClient, WebSocketClient


# overload_inject_start_client
@overload
def Client(
    *,
    asyncio: Optional[bool] = False,
    host: Optional[str] = '0.0.0.0',
    port: Optional[int] = None,
    protocol: Optional[str] = 'GRPC',
    proxy: Optional[bool] = False,
    tls: Optional[bool] = False,
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
    :param port: The port of the Gateway, which the client should connect to.
    :param protocol: Communication protocol between server and client.
    :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
    :param tls: If set, connect to gateway using tls encryption
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
    # implementation_stub_inject_start_client

    """Convenience function that returns client instance for given protocol.

    EXAMPLE USAGE

    .. code-block:: python

        from jina import Client
        from docarray import Document

        # select protocol from 'grpc', 'http', or 'websocket'; default is 'grpc'
        # select asyncio True of False; default is False
        # select host address to connect to
        c = Client(
            protocol='grpc', asyncio=False, host='grpc://my.awesome.flow:1234'
        )  # returns GRPCClient instance
        c.post(on='/index', inputs=Document(text='hello!'))

    :param asyncio: If set, then the input and output of this Client work in an asynchronous manner.
    :param host: The host address of the runtime, by default it is 0.0.0.0.
    :param port: The port of the Gateway, which the client should connect to.
    :param protocol: Communication protocol between server and client.
    :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
    :param tls: If set, connect to gateway using tls encryption
    :return: the new Client object

    .. # noqa: DAR102
    .. # noqa: DAR202
    .. # noqa: DAR101
    .. # noqa: DAR003
    """
    # implementation_stub_inject_end_client
    if not (
        args and isinstance(args, argparse.Namespace)
    ):  # we need to parse the kwargs as soon as possible otherwise to get the gateway type
        args = parse_client(kwargs)

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
