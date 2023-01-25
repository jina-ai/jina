from dataclasses import dataclass
from typing import Dict, Optional

import grpc
from opentelemetry.metrics import Histogram
from prometheus_client import Summary


@dataclass
class _NetworkingMetrics:
    """
    dataclass that contain the metrics used in the networking part
    """

    sending_requests_time_metrics: Optional['Summary']
    received_response_bytes: Optional['Summary']
    send_requests_bytes_metrics: Optional['Summary']


@dataclass
class _NetworkingHistograms:
    """
    Dataclass containing the various OpenTelemetry Histograms for measuring the network level operations.
    """

    sending_requests_time_metrics: Optional['Histogram'] = None
    received_response_bytes: Optional['Histogram'] = None
    send_requests_bytes_metrics: Optional['Histogram'] = None
    histogram_metric_labels: Dict[str, str] = None

    def _get_labels(
        self, additional_labels: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, str]]:

        if self.histogram_metric_labels is None:
            return None
        if additional_labels is None:
            return self.histogram_metric_labels
        return {**self.histogram_metric_labels, **additional_labels}

    def record_sending_requests_time_metrics(
        self, value: int, additional_labels: Optional[Dict[str, str]] = None
    ):
        labels = self._get_labels(additional_labels)

        if self.sending_requests_time_metrics:
            self.sending_requests_time_metrics.record(value, labels)

    def record_received_response_bytes(
        self, value: int, additional_labels: Optional[Dict[str, str]] = None
    ):
        labels = self._get_labels(additional_labels)

        if self.received_response_bytes:
            self.received_response_bytes.record(value, labels)

    def record_send_requests_bytes_metrics(
        self, value: int, additional_labels: Optional[Dict[str, str]] = None
    ):
        labels = self._get_labels(additional_labels)

        if self.send_requests_bytes_metrics:
            self.send_requests_bytes_metrics.record(value, labels)


def _aio_channel_with_tracing_interceptor(
    address,
    credentials=None,
    options=None,
    interceptors=None,
) -> grpc.aio.Channel:
    if credentials:
        return grpc.aio.secure_channel(
            address,
            credentials,
            options=options,
            interceptors=interceptors,
        )
    return grpc.aio.insecure_channel(
        address,
        options=options,
        interceptors=interceptors,
    )


def _channel_with_tracing_interceptor(
    address,
    credentials=None,
    options=None,
    interceptor=None,
) -> grpc.Channel:
    if credentials:
        channel = grpc.secure_channel(address, credentials, options=options)
    else:
        channel = grpc.insecure_channel(address, options=options)

    if interceptor:
        from opentelemetry.instrumentation.grpc.grpcext import intercept_channel

        return intercept_channel(
            channel,
            interceptor,
        )
    else:
        return channel
