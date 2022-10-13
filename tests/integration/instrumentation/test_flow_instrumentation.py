import time

import pytest

from jina import Flow
from tests.integration.instrumentation import (
    ExecutorFailureWithTracing,
    ExecutorTestWithTracing,
    get_exported_jobs,
    get_flow_metric_labels,
    get_histogram_rate_and_exported_jobs_by_name,
    get_metrics_and_exported_jobs_by_name,
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


def test_flow_metrics(
    otlp_collector,
    prometheus_client,
    set_metrics_export_interval,
    expected_flow_metric_labels,
    instrumented_services_sharded,
):
    f = Flow(
        metrics=True,
        metrics_exporter_host='localhost',
        metrics_exporter_port=4317,
    ).add(
        uses=ExecutorFailureWithTracing,
        shards=2,
        metrics=True,
        metrics_exporter_host='localhost',
        metrics_exporter_port=4317,
    )

    with f:
        from jina import DocumentArray

        f.post(
            f'/index', DocumentArray.empty(2), request_size=1, continue_on_error=True
        )
        f.post(
            f'/index', DocumentArray.empty(2), request_size=1, continue_on_error=True
        )
        # give some time for the tracing and metrics exporters to finish exporting.
        # the client is slow to export the data
        time.sleep(8)

    exported_jobs = get_exported_jobs(prometheus_client)
    assert exported_jobs.issubset(instrumented_services_sharded)

    flow_metric_labels = get_flow_metric_labels(prometheus_client)
    assert flow_metric_labels.issubset(expected_flow_metric_labels)

    (
        sending_requests_seconds_metrics,
        sending_requests_seconds_exported_jobs,
    ) = get_histogram_rate_and_exported_jobs_by_name(
        prometheus_client, 'sending_request_seconds'
    )
    # TODO
    # assert len(sending_requests_seconds_metrics) == 0
    # assert sending_requests_seconds_exported_jobs.issubset(['gateway/rep-0', 'executor0/head'])

    (
        receiving_request_seconds_metrics,
        receiving_request_seconds_exported_jobs,
    ) = get_histogram_rate_and_exported_jobs_by_name(
        prometheus_client, 'receiving_request_seconds'
    )
    # TODO
    # assert len(receiving_request_seconds_metrics) == 0
    # assert receiving_request_seconds_exported_jobs.issubset(['gateway/rep-0', 'executor0/head'])

    (
        received_response_bytes_metrics,
        received_response_bytes_exported_jobs,
    ) = get_histogram_rate_and_exported_jobs_by_name(
        prometheus_client, 'received_response_bytes'
    )
    assert len(received_response_bytes_metrics) > 0
    assert received_response_bytes_exported_jobs.issubset(
        ['gateway/rep-0', 'executor0/head']
    )

    (
        sent_requests_bytes_metrics,
        sent_requests_bytes_exported_jobs,
    ) = get_histogram_rate_and_exported_jobs_by_name(
        prometheus_client, 'sent_request_bytes'
    )
    assert len(sent_requests_bytes_metrics) > 0
    assert sent_requests_bytes_exported_jobs.issubset(
        ['gateway/rep-0', 'executor0/head']
    )

    (
        sent_response_bytes_metrics,
        sent_response_bytes_exported_jobs,
    ) = get_histogram_rate_and_exported_jobs_by_name(
        prometheus_client, 'sent_response_bytes'
    )
    assert len(sent_response_bytes_metrics) > 0
    assert sent_response_bytes_exported_jobs.issubset(
        ['gateway/rep-0', 'executor0/head']
    )

    (
        number_of_pending_requests_metrics,
        number_of_pending_requests_exported_jobs,
    ) = get_metrics_and_exported_jobs_by_name(
        prometheus_client, 'number_of_pending_requests'
    )
    assert len(number_of_pending_requests_metrics) > 0
    assert number_of_pending_requests_exported_jobs.issubset(['gateway/rep-0'])

    (
        failed_requests_metrics,
        failed_requests_exported_jobs,
    ) = get_metrics_and_exported_jobs_by_name(prometheus_client, 'failed_requests')
    assert len(failed_requests_metrics) > 0
    assert failed_requests_exported_jobs.issubset(['gateway/rep-0'])

    (
        successful_requests_metrics,
        successful_requests_exported_jobs,
    ) = get_metrics_and_exported_jobs_by_name(prometheus_client, 'successful_requests')
    assert len(successful_requests_metrics) > 0
    assert successful_requests_exported_jobs.issubset(['gateway/rep-0'])

    (
        received_request_bytes_metrics,
        received_request_bytes_exported_jobs,
    ) = get_histogram_rate_and_exported_jobs_by_name(
        prometheus_client, 'received_request_bytes'
    )
    assert len(received_request_bytes_metrics) > 0
    assert received_request_bytes_exported_jobs.issubset(
        ['gateway/rep-0', 'executor0/head']
    )
