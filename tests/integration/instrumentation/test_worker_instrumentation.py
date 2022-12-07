import time

from jina import Flow
from tests.integration.instrumentation import ExecutorTestWithTracing, get_traces


def test_span_order(jaeger_port, otlp_collector, otlp_receiver_port):
    f = Flow(
        tracing=True,
        traces_exporter_host='http://localhost',
        traces_exporter_port=otlp_receiver_port,
    ).add(uses=ExecutorTestWithTracing)

    with f:
        from jina import DocumentArray

        f.post(f'/search', DocumentArray.empty(), continue_on_error=True)
        # give some time for the tracing and metrics exporters to finish exporting.
        # the client is slow to export the data
        time.sleep(8)

    traces = get_traces(jaeger_port, 'executor0/rep-0')
    process_single_data_span_ids = set()
    search_request_parent_span_ids = set()
    for trace in traces:
        for span in trace['spans']:
            if (
                span['operationName']
                == '/jina.JinaSingleDataRequestRPC/process_single_data'
            ):
                process_single_data_span_ids.add(span['spanID'])

            if span['operationName'] == '/search':
                references = span.get('references', [])
                for ref in references:
                    search_request_parent_span_ids.add(ref.get('spanID', ''))

    assert any(
        [
            search_span in process_single_data_span_ids
            for search_span in search_request_parent_span_ids
        ]
    )
