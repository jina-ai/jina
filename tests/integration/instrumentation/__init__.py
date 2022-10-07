from typing import Dict, Optional

from docarray import DocumentArray
from opentelemetry.context.context import Context

from jina import Executor, requests


def get_traces(service):
    import requests

    response = requests.get(f'http://localhost:16686/api/traces?service={service}')
    response.raise_for_status()
    return response.json().get('data', []) or []


def _get_trace_id(any_object):
    return any_object.get('traceID', '')


def get_trace_ids(traces):
    trace_ids = set()
    for trace in traces:
        trace_ids.add(_get_trace_id(trace))
        for span in trace['spans']:
            trace_ids.add(_get_trace_id(span))

    return trace_ids


def partition_spans_by_kind(traces):
    '''Returns three lists each containing spans of kind SpanKind.SERVER, SpanKind.CLIENT and SpandKind.INTERNAL'''
    server_spans = []
    client_spans = []
    internal_spans = []

    for trace in traces:
        for span in trace['spans']:
            for tag in span['tags']:
                if 'span.kind' == tag.get('key', ''):
                    span_kind = tag.get('value', '')
                    if 'server' == span_kind:
                        server_spans.append(span)
                    elif 'client' == span_kind:
                        client_spans.append(span)
                    elif 'internal' == span_kind:
                        internal_spans.append(span)

    return (server_spans, client_spans, internal_spans)


class ExecutorTestWithTracing(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_counter = self.meter.create_counter(name='docs_counter')

    @requests(on='/index')
    def empty(self, docs: 'DocumentArray', tracing_context: Context, **kwargs):
        with self.tracer.start_as_current_span(
            'dummy', context=tracing_context
        ) as span:
            span.set_attribute('len_docs', len(docs))
            self.docs_counter.add(len(docs))
            return docs


def get_services():
    import requests

    response = requests.get('http://localhost:16686/api/services')
    response.raise_for_status()
    response_json = response.json()
    services = response_json.get('data', []) or []
    return [service for service in services if service != 'jaeger-query']
