from typing import Dict, List, Tuple

import pytest
from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    HistogramDataPoint,
    InMemoryMetricReader,
    Metric,
)

from jina.serve.networking.instrumentation import _NetworkingHistograms


@pytest.fixture
def metrics_setup() -> Tuple[InMemoryMetricReader, MeterProvider]:
    metric_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    meter = meter_provider.get_meter('test')
    yield metric_reader, meter
    if hasattr(meter_provider, 'force_flush'):
        metric_reader.force_flush()
    if hasattr(meter_provider, 'shutdown'):
        meter_provider.shutdown()


def test_get_labels():
    a: _NetworkingHistograms = _NetworkingHistograms()
    assert a._get_labels() == None

    HIST_LABELS = {
        'a': 1,
        'b': 2,
    }
    a.histogram_metric_labels = HIST_LABELS
    assert a._get_labels() == HIST_LABELS

    ADD_LABELS = {
        'b': 3,
        'c': 4,
    }
    assert a._get_labels(ADD_LABELS) == {**HIST_LABELS, **ADD_LABELS}


def test_recording_methods(metrics_setup: Tuple[InMemoryMetricReader, Meter]):
    metric_reader, meter = metrics_setup

    a: _NetworkingHistograms = _NetworkingHistograms(
        sending_requests_time_metrics=meter.create_histogram("request_time"),
        send_requests_bytes_metrics=meter.create_histogram("request_bytes"),
        received_response_bytes=meter.create_histogram("response_bytes"),
        histogram_metric_labels=None,
    )

    a.record_sending_requests_time_metrics(10)
    a.record_send_requests_bytes_metrics(20)
    a.record_received_response_bytes(30)

    histogram_metrics: List[Metric] = (
        metric_reader.get_metrics_data().resource_metrics[0].scope_metrics[0].metrics
    )
    data_points_sums: Dict[str, HistogramDataPoint] = {
        hist.name: next(iter(hist.data.data_points)).sum for hist in histogram_metrics
    }
    assert data_points_sums == {
        'request_time': 10,
        'request_bytes': 20,
        'response_bytes': 30,
    }
