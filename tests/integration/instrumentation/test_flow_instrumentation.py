import time

import pytest

from jina import Flow
from tests.integration.instrumentation import (
    ExecutorFailureWithTracing,
    ExecutorTestWithTracing,
    get_services,
    get_trace_ids,
    get_traces,
    partition_spans_by_kind,
    spans_with_error,
)


@pytest.mark.parametrize(
    'protocol, client_type, num_internal_spans',
    [
        ('grpc', 'GRPCClient', 2),
        ('http', 'HTTPClient', 5),
        ('websocket', 'WebSocketClient', 7),
    ],
)
def test_gateway_instrumentation(
    otlp_collector, protocol, client_type, num_internal_spans
):
    f = Flow(
        protocol=protocol,
        tracing=True,
        traces_exporter_host='localhost',
        traces_exporter_port=4317,
    ).add(
        uses=ExecutorTestWithTracing,
        tracing=True,
        traces_exporter_host='localhost',
        traces_exporter_port=4317,
    )

    with f:
        from jina import DocumentArray

        f.post(f'/index', DocumentArray.empty(2), continue_on_error=True)
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


def test_executor_instrumentation(otlp_collector):
    f = Flow(
        tracing=True,
        traces_exporter_host='localhost',
        traces_exporter_port=4317,
    ).add(uses=ExecutorFailureWithTracing)

    with f:
        from jina import DocumentArray

        f.post(f'/index', DocumentArray.empty(2), continue_on_error=True)
        # give some time for the tracing and metrics exporters to finish exporting.
        # the client is slow to export the data
        time.sleep(8)

    client_type = 'GRPCClient'
    client_traces = get_traces(client_type)
    (server_spans, client_spans, internal_spans) = partition_spans_by_kind(
        client_traces
    )
    assert len(spans_with_error(server_spans)) == 0
    assert len(spans_with_error(client_spans)) == 0
    assert len(internal_spans) == 2
    # Errors reported by DataRequestHandler and request method level spans
    assert len(spans_with_error(internal_spans)) == 2

    trace_ids = get_trace_ids(client_traces)
    assert len(trace_ids) == 1


def test_head_instrumentation(otlp_collector):
    f = Flow(
        tracing=True,
        traces_exporter_host='localhost',
        traces_exporter_port=4317,
    ).add(uses=ExecutorTestWithTracing, shards=2)

    with f:
        from jina import DocumentArray

        f.post(f'/index', DocumentArray.empty(2), continue_on_error=True)
        # give some time for the tracing and metrics exporters to finish exporting.
        # the client is slow to export the data
        time.sleep(8)

    client_type = 'GRPCClient'
    client_traces = get_traces(client_type)
    (server_spans, client_spans, internal_spans) = partition_spans_by_kind(
        client_traces
    )
    assert len(server_spans) == 9
    assert len(client_spans) == 9
    assert len(internal_spans) == 2

    services = get_services()
    expected_services = [
        'executor0/shard-0/rep-0',
        'executor0/shard-1/rep-0',
        'gateway/rep-0',
        'executor0/head',
        client_type,
    ]
    assert len(services) == 5
    assert set(services).issubset(expected_services)

    trace_ids = get_trace_ids(client_traces)
    assert len(trace_ids) == 1
