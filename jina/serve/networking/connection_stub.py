from collections import defaultdict
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple

import grpc

from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.instrumentation import MetricsTimer
from jina.serve.networking.instrumentation import (
    _NetworkingHistograms,
    _NetworkingMetrics,
)
from jina.serve.networking.utils import get_available_services, get_grpc_channel
from jina.types.request import Request
from jina.types.request.data import DataRequest

if TYPE_CHECKING:  # pragma: no cover
    from grpc.aio._interceptor import ClientInterceptor


class _ConnectionStubs:
    """
    Maintains a list of grpc stubs available for a particular connection
    """

    STUB_MAPPING = {
        'jina.JinaDataRequestRPC': jina_pb2_grpc.JinaDataRequestRPCStub,
        'jina.JinaSingleDataRequestRPC': jina_pb2_grpc.JinaSingleDataRequestRPCStub,
        'jina.JinaDiscoverEndpointsRPC': jina_pb2_grpc.JinaDiscoverEndpointsRPCStub,
        'jina.JinaRPC': jina_pb2_grpc.JinaRPCStub,
        'jina.JinaInfoRPC': jina_pb2_grpc.JinaInfoRPCStub,
    }

    def __init__(
        self,
        address,
        channel,
        deployment_name: str,
        metrics: _NetworkingMetrics,
        histograms: _NetworkingHistograms,
    ):
        self.address = address
        self.channel = channel
        self.deployment_name = deployment_name
        self._metrics = metrics
        self._histograms = histograms
        self._initialized = False

        if self._histograms:
            self.stub_specific_labels = {
                'deployment': deployment_name,
                'address': address,
            }

    # This has to be done lazily, because the target endpoint may not be available
    # when a connection is added
    async def _init_stubs(self):
        available_services = await get_available_services(self.channel)
        stubs = defaultdict(lambda: None)
        for service in available_services:
            stubs[service] = self.STUB_MAPPING[service](self.channel)
        self.data_list_stub = stubs['jina.JinaDataRequestRPC']
        self.single_data_stub = stubs['jina.JinaSingleDataRequestRPC']
        self.stream_stub = stubs['jina.JinaRPC']
        self.endpoints_discovery_stub = stubs['jina.JinaDiscoverEndpointsRPC']
        self.info_rpc_stub = stubs['jina.JinaInfoRPC']
        self._initialized = True

    async def send_discover_endpoint(
        self,
        timeout: Optional[float] = None,
    ) -> Tuple:
        """
        Use the endpoint discovery stub to request for the Endpoints Exposed by an Executor

        :param timeout: defines timeout for sending request

        :returns: Tuple of response and metadata about the response
        """
        if not self._initialized:
            await self._init_stubs()

        call_result = self.endpoints_discovery_stub.endpoint_discovery(
            jina_pb2.google_dot_protobuf_dot_empty__pb2.Empty(),
            timeout=timeout,
        )
        metadata, response = (
            await call_result.trailing_metadata(),
            await call_result,
        )
        return response, metadata

    def _get_metric_timer(self):
        if self._histograms.histogram_metric_labels is None:
            labels = None
        else:
            labels = {
                **self._histograms.histogram_metric_labels,
                **self.stub_specific_labels,
            }

        return MetricsTimer(
            self._metrics.sending_requests_time_metrics,
            self._histograms.sending_requests_time_metrics,
            labels,
        )

    def _record_request_bytes_metric(self, nbytes: int):
        if self._metrics.send_requests_bytes_metrics:
            self._metrics.send_requests_bytes_metrics.observe(nbytes)
        self._histograms.record_send_requests_bytes_metrics(
            nbytes, self.stub_specific_labels
        )

    def _record_received_bytes_metric(self, nbytes: int):
        if self._metrics.received_response_bytes:
            self._metrics.received_response_bytes.observe(nbytes)
        self._histograms.record_received_response_bytes(
            nbytes, self.stub_specific_labels
        )

    async def send_requests(
        self,
        requests: List[Request],
        metadata,
        compression,
        timeout: Optional[float] = None,
    ) -> Tuple:
        """
        Send requests and uses the appropriate grpc stub for this
        Stub is chosen based on availability and type of requests

        :param requests: the requests to send
        :param metadata: the metadata to send alongside the requests
        :param compression: defines if compression should be used
        :param timeout: defines timeout for sending request

        :returns: Tuple of response and metadata about the response
        """
        if not self._initialized:
            await self._init_stubs()
        request_type = type(requests[0])

        timer = self._get_metric_timer()
        if request_type == DataRequest and len(requests) == 1:
            request = requests[0]
            if self.single_data_stub:
                self._record_request_bytes_metric(request.nbytes)
                call_result = self.single_data_stub.process_single_data(
                    request,
                    metadata=metadata,
                    compression=compression,
                    timeout=timeout,
                )
                with timer:
                    metadata, response = (
                        await call_result.trailing_metadata(),
                        await call_result,
                    )
                    self._record_received_bytes_metric(response.nbytes)
                return response, metadata

            elif self.stream_stub:
                self._record_request_bytes_metric(request.nbytes)

                with timer:
                    async for response in self.stream_stub.Call(
                        iter(requests),
                        compression=compression,
                        timeout=timeout,
                        metadata=metadata,
                    ):
                        self._record_received_bytes_metric(response.nbytes)
                        return response, None

        if request_type == DataRequest and len(requests) > 1:
            if self.data_list_stub:
                for request in requests:
                    self._record_request_bytes_metric(request.nbytes)
                call_result = self.data_list_stub.process_data(
                    requests,
                    metadata=metadata,
                    compression=compression,
                    timeout=timeout,
                )
                with timer:
                    metadata, response = (
                        await call_result.trailing_metadata(),
                        await call_result,
                    )
                    self._record_received_bytes_metric(response.nbytes)
                return response, metadata
            else:
                raise ValueError(
                    'Can not send list of DataRequests. gRPC endpoint not available.'
                )
        else:
            raise ValueError(f'Unsupported request type {type(requests[0])}')

    async def send_info_rpc(self, timeout: Optional[float] = None):
        """
        Use the JinaInfoRPC stub to send request to the _status endpoint exposed by the Runtime
        :param timeout: defines timeout for sending request
        :returns: JinaInfoProto
        """
        if not self._initialized:
            await self._init_stubs()

        call_result = self.info_rpc_stub._status(
            jina_pb2.google_dot_protobuf_dot_empty__pb2.Empty(),
            timeout=timeout,
        )
        return await call_result


def create_async_channel_stub(
    address,
    deployment_name: str,
    metrics: _NetworkingMetrics,
    histograms: _NetworkingHistograms,
    tls=False,
    root_certificates: Optional[str] = None,
    aio_tracing_client_interceptors: Optional[Sequence['ClientInterceptor']] = None,
) -> Tuple[_ConnectionStubs, grpc.aio.Channel]:
    """
    Creates an async GRPC Channel. This channel has to be closed eventually!

    :param address: the address to create the connection to, like 126.0.0.0.1:8080
    :param deployment_name: the name of the deployment (e.g. executor-1)
    :param tls: if True, use tls for the grpc channel
    :param root_certificates: the path to the root certificates for tls, only u
    :param metrics: NetworkingMetrics object that contain optional metrics
    :param histograms: NetworkingHistograms object that optionally record metrics
    :param aio_tracing_client_interceptors: List of async io gprc client tracing interceptors for tracing requests for asycnio channel
    :returns: DataRequest stubs and an async grpc channel
    """
    channel = get_grpc_channel(
        address,
        asyncio=True,
        tls=tls,
        root_certificates=root_certificates,
        aio_tracing_client_interceptors=aio_tracing_client_interceptors,
    )

    return (
        _ConnectionStubs(address, channel, deployment_name, metrics, histograms),
        channel,
    )
