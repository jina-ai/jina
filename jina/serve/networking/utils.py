import ipaddress
import os
from typing import TYPE_CHECKING, List, Optional, Sequence

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha.reflection_pb2 import ServerReflectionRequest
from grpc_reflection.v1alpha.reflection_pb2_grpc import ServerReflectionStub

from jina.proto import jina_pb2_grpc
from jina.serve.networking.instrumentation import (
    _aio_channel_with_tracing_interceptor,
    _channel_with_tracing_interceptor,
)
from jina.types.request import Request

if TYPE_CHECKING:  # pragma: no cover
    from grpc.aio._interceptor import ClientInterceptor
    from opentelemetry.instrumentation.grpc._client import (
        OpenTelemetryClientInterceptor,
    )


def get_grpc_channel(
    address: str,
    options: Optional[list] = None,
    asyncio: bool = False,
    tls: bool = False,
    root_certificates: Optional[str] = None,
    aio_tracing_client_interceptors: Optional[Sequence['ClientInterceptor']] = None,
    tracing_client_interceptor: Optional['OpenTelemetryClientInterceptor'] = None,
) -> grpc.Channel:
    """
    Creates a grpc channel to the given address

    :param address: The address to connect to, format is <host>:<port>
    :param options: A list of options to pass to the grpc channel
    :param asyncio: If True, use the asyncio implementation of the grpc channel
    :param tls: If True, use tls encryption for the grpc channel
    :param root_certificates: The path to the root certificates for tls, only used if tls is True
    :param aio_tracing_client_interceptors: List of async io gprc client tracing interceptors for tracing requests if asycnio is True
    :param tracing_client_interceptor: A gprc client tracing interceptor for tracing requests if asyncio is False
    :return: A grpc channel or an asyncio channel
    """

    if options is None:
        options = get_default_grpc_options()

    credentials = None
    if tls:
        credentials = grpc.ssl_channel_credentials(root_certificates=root_certificates)

    if asyncio:
        return _aio_channel_with_tracing_interceptor(
            address, credentials, options, aio_tracing_client_interceptors
        )

    return _channel_with_tracing_interceptor(
        address, credentials, options, tracing_client_interceptor
    )


def send_request_sync(
    request: Request,
    target: str,
    timeout=99.0,
    tls=False,
    root_certificates: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> Request:
    """
    Sends a request synchronously to the target via grpc

    :param request: the request to send
    :param target: where to send the request to, like 126.0.0.1:8080
    :param timeout: timeout for the send
    :param tls: if True, use tls encryption for the grpc channel
    :param root_certificates: the path to the root certificates for tls, only used if tls is True
    :param endpoint: endpoint to target with the request

    :returns: the response request
    """

    for i in range(2):
        try:
            with get_grpc_channel(
                target,
                tls=tls,
                root_certificates=root_certificates,
            ) as channel:
                metadata = (('endpoint', endpoint),) if endpoint else None
                stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
                response, call = stub.process_single_data.with_call(
                    request,
                    timeout=timeout,
                    metadata=metadata,
                )
                return response
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.UNAVAILABLE or i == 1:
                raise


def send_health_check_sync(
    target: str,
    timeout=99.0,
    tls=False,
    root_certificates: Optional[str] = None,
) -> health_pb2.HealthCheckResponse:
    """
    Sends a request synchronously to the target via grpc

    :param target: where to send the request to, like 126.0.0.1:8080
    :param timeout: timeout for the send
    :param tls: if True, use tls encryption for the grpc channel
    :param root_certificates: the path to the root certificates for tls, only used if tls is True

    :returns: the response health check
    """

    for i in range(2):
        try:
            with get_grpc_channel(
                target,
                tls=tls,
                root_certificates=root_certificates,
            ) as channel:
                health_check_req = health_pb2.HealthCheckRequest()
                health_check_req.service = ''
                stub = health_pb2_grpc.HealthStub(channel)
                return stub.Check(health_check_req, timeout=timeout)
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.UNAVAILABLE or i == 1:
                raise


async def send_health_check_async(
    target: str,
    timeout=99.0,
    tls=False,
    root_certificates: Optional[str] = None,
) -> health_pb2.HealthCheckResponse:
    """
    Sends a request asynchronously to the target via grpc
    :param target: where to send the request to, like 126.0.0.1:8080
    :param timeout: timeout for the send
    :param tls: if True, use tls encryption for the grpc channel
    :param root_certificates: the path to the root certificates for tls, only used if tls is True
    :returns: the response health check
    """

    for i in range(2):
        try:
            async with get_grpc_channel(
                target,
                tls=tls,
                asyncio=True,
                root_certificates=root_certificates,
            ) as channel:
                health_check_req = health_pb2.HealthCheckRequest()
                health_check_req.service = ''
                stub = health_pb2_grpc.HealthStub(channel)
                return await stub.Check(health_check_req, timeout=timeout)
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.UNAVAILABLE or i == 1:
                raise
        except Exception as e:
            raise e


def send_requests_sync(
    requests: List[Request],
    target: str,
    timeout=99.0,
    tls=False,
    root_certificates: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> Request:
    """
    Sends a list of requests synchronically to the target via grpc

    :param requests: the requests to send
    :param target: where to send the request to, like 126.0.0.1:8080
    :param timeout: timeout for the send
    :param tls: if True, use tls for the grpc channel
    :param root_certificates: the path to the root certificates for tls, only used if tls is True
    :param endpoint: endpoint to target with the request

    :returns: the response request
    """

    for i in range(2):
        try:
            with get_grpc_channel(
                target,
                tls=tls,
                root_certificates=root_certificates,
            ) as channel:
                metadata = (('endpoint', endpoint),) if endpoint else None
                stub = jina_pb2_grpc.JinaDataRequestRPCStub(channel)
                response, call = stub.process_data.with_call(
                    requests,
                    timeout=timeout,
                    metadata=metadata,
                )
                return response
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.UNAVAILABLE or i == 1:
                raise


def get_default_grpc_options():
    """
    Returns a list of default options used for creating grpc channels.
    Documentation is here https://github.com/grpc/grpc/blob/master/include/grpc/impl/codegen/grpc_types.h
    :returns: list of tuples defining grpc parameters
    """

    return [
        ('grpc.max_send_message_length', -1),
        ('grpc.max_receive_message_length', -1),
        # for the following see this blog post for the choice of default value https://cs.mcgill.ca/~mxia2/2019/02/23/Using-gRPC-in-Production/
        ('grpc.keepalive_time_ms', 9999),
        # send keepalive ping every 9 second, default is 2 hours.
        ('grpc.keepalive_timeout_ms', 4999),
        # keepalive ping time out after 4 seconds, default is 20 seconds
        ('grpc.keepalive_permit_without_calls', True),
        # allow keepalive pings when there's no gRPC calls
        ('grpc.http1.max_pings_without_data', 0),
        # allow unlimited amount of keepalive pings without data
        ('grpc.http1.min_time_between_pings_ms', 10000),
        # allow grpc pings from client every 9 seconds
        ('grpc.http1.min_ping_interval_without_data_ms', 5000),
        # allow grpc pings from client without data every 4 seconds
    ]


async def send_request_async(
    request: Request,
    target: str,
    timeout: float = 0.0,
    tls: bool = False,
    root_certificates: Optional[str] = None,
) -> Request:
    """
    Sends a request asynchronously to the target via grpc

    :param request: the request to send
    :param target: where to send the request to, like 126.0.0.1:8080
    :param timeout: timeout for the send
    :param tls: if True, use tls for the grpc channel
    :param root_certificates: the path to the root certificates for tls, only used if tls is True

    :returns: the response request
    """

    async with get_grpc_channel(
        target,
        asyncio=True,
        tls=tls,
        root_certificates=root_certificates,
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        return await stub.process_single_data(request, timeout=timeout)


async def get_available_services(channel) -> List[str]:
    """
    Lists available services by name, exposed at target address

    :param channel: the channel to use

    :returns: List of services offered
    """
    reflection_stub = ServerReflectionStub(channel)
    response = reflection_stub.ServerReflectionInfo(
        iter([ServerReflectionRequest(list_services="")])
    )
    service_names = []
    async for res in response:
        service_names.append(
            [
                service.name
                for service in res.list_services_response.service
                if service.name
                not in {
                    'grpc.reflection.v1alpha.ServerReflection',
                    'jina.JinaGatewayDryRunRPC',
                }
            ]
        )
    return service_names[-1]


TLS_PROTOCOL_SCHEMES = ['grpcs', 'https', 'wss']
DEFAULT_MINIMUM_RETRIES = 3


def in_docker():
    """
    Checks if the current process is running inside Docker
    :return: True if the current process is running inside Docker
    """
    path = '/proc/self/cgroup'
    if os.path.exists('/.dockerenv'):
        return True
    if os.path.isfile(path):
        with open(path) as file:
            return any('docker' in line for line in file)
    return False


def host_is_local(hostname):
    """
    Check if hostname is point to localhost
    :param hostname: host to check
    :return: True if hostname means localhost, False otherwise
    """
    import socket

    fqn = socket.getfqdn(hostname)
    if fqn in ('localhost', '0.0.0.0') or hostname == '0.0.0.0':
        return True

    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False
