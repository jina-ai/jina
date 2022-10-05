import time
from audioop import mul

import pytest

from jina import Client, Flow
from tests.integration.instrumentation import (
    ExecutorTestWithTracing,
    get_services,
    get_trace_ids,
    get_traces,
    partition_spans_by_kind,
)


@pytest.mark.skip
def test_websocket_gateway_instrumentation(logger, otlp_collector):
    f = Flow(
        protocol='websocket',
        opentelemetry_tracing=True,
        span_exporter_host='localhost',
        span_exporter_port=4317,
    ).add(
        uses=ExecutorTestWithTracing,
        opentelemetry_tracing=True,
        span_exporter_host='localhost',
        span_exporter_port=4317,
    )

    f.start()

    c = Client(
        host=f'ws://localhost:{f.port}',
        opentelemetry_tracing=True,
        span_exporter_host='localhost',
        span_exporter_port=4317,
    )
    c.post(
        f'/index',
        {'data': [{'text': 'text_input'}]},
    )

    # give some time for the tracing and metrics exporters to finish exporting.
    # the client is slow to export the data
    logger.info('waiting until traces and metrics are exported...')
    time.sleep(8)
    f.close()

    services = get_services()
    expected_services = ['executor0/rep-0', 'gateway/rep-0', 'WebSocketClient']
    assert len(services) == 3
    assert set(services).issubset(expected_services)

    client_traces = get_traces('WebSocketClient')
    (server_spans, client_spans, internal_spans) = partition_spans_by_kind(
        client_traces
    )
    assert len(server_spans) == 5
    assert len(client_spans) == 5
    assert len(internal_spans) == 6

    trace_ids = get_trace_ids(client_traces)
    assert len(trace_ids) == 1
