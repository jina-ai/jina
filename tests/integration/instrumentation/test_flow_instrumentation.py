import time

import pytest

from jina import Flow
from tests.integration.instrumentation import (
    ExecutorTestWithTracing,
    get_services,
    get_trace_ids,
    get_traces,
    partition_spans_by_kind,
)


@pytest.mark.parametrize(
    'protocol, client_type, num_internal_spans',
    [
        ('grpc', 'GRPCClient', 1),
        ('http', 'HTTPClient', 4),
        ('websocket', 'WebSocketClient', 6),
    ],
)
def test_gateway_instrumentation(
    otlp_collector, protocol, client_type, num_internal_spans
):
    f = Flow(
        protocol=protocol,
        tracing=True,
        span_exporter_host='localhost',
        span_exporter_port=4317,
    ).add(
        uses=ExecutorTestWithTracing,
        tracing=True,
        span_exporter_host='localhost',
        span_exporter_port=4317,
    )

    with f:
        from jina import DocumentArray

        f.post(
            f'/index',
            DocumentArray.empty(2),
        )
        # give some time for the tracing and metrics exporters to finish exporting.
        # the client is slow to export the data
        time.sleep(8)

    services = get_services()
    expected_services = ['executor0/rep-0', 'gateway/rep-0', client_type]
    assert len(services) == 3
    assert set(services).issubset(expected_services)

    client_traces = get_traces(client_type)
    (server_spans, client_spans, internal_spans) = partition_spans_by_kind(
        client_traces
    )
    assert len(server_spans) == 5
    assert len(client_spans) == 5
    assert len(internal_spans) == num_internal_spans

    trace_ids = get_trace_ids(client_traces)
    assert len(trace_ids) == 1
