from typing import Optional

import requests as http_requests
from docarray import DocumentArray
from opentelemetry.context.context import Context

from jina import Executor, requests


def get_traces(service):
    response = http_requests.get(f'http://localhost:16686/api/traces?service={service}')
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
        if self.meter:
            self.request_counter = self.meter.create_counter('request_counter')
        else:
            self.request_counter = None

    @requests(on='/index')
    def empty(
        self, docs: 'DocumentArray', tracing_context: Optional[Context], **kwargs
    ):
        if self.request_counter:
            self.request_counter.add(1)

        if self.tracer:
            with self.tracer.start_span('dummy', context=tracing_context) as span:
                span.set_attribute('len_docs', len(docs))
                return docs
        else:
            return docs


def get_services():
    response = http_requests.get('http://localhost:16686/api/services')
    response.raise_for_status()
    response_json = response.json()
    services = response_json.get('data', []) or []
    return [service for service in services if service != 'jaeger-query']


class ExecutorFailureWithTracing(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failure_counter = 0

    @requests(on='/index')
    def empty(
        self, docs: 'DocumentArray', tracing_context: Optional[Context], **kwargs
    ):
        if self.tracer:
            with self.tracer.start_span('dummy', context=tracing_context) as span:
                span.set_attribute('len_docs', len(docs))
                if not self.failure_counter:
                    self.failure_counter += 1
                    raise NotImplementedError
                else:
                    return docs
        else:
            return docs


def spans_with_error(spans):
    error_spans = []
    for span in spans:
        for tag in span['tags']:
            if 'otel.status_code' == tag.get('key', '') and 'ERROR' == tag.get(
                'value', ''
            ):
                error_spans.append(span)
    return error_spans


def get_metrics_by_name(metric_name: str):
    response = http_requests.get(
        f'http://localhost:9090/api/v1/query?query={metric_name}'
    )
    response.raise_for_status()
    return response.json().get('data', {}).get('result', []) or []


def get_all_metric_labels():
    response = http_requests.get('http://localhost:9090/api/v1/label/__name__/values')
    response.raise_for_status()
    return response.json().get('data', []) or []


def get_histogram_rate_and_exported_jobs_by_name(metric_name: str):
    response = http_requests.get(
        f'http://localhost:9090/api/v1/query?query=rate({metric_name}_bucket[1m])'
    )
    response.raise_for_status()
    metrics = response.json().get('data', {}).get('result', []) or []
    exported_jobs = set([metric['metric']['exported_job'] for metric in metrics])
    return metrics, exported_jobs


def get_exported_jobs():
    response = http_requests.get(
        'http://localhost:9090/api/v1/label/exported_job/values'
    )
    response.raise_for_status()
    return response.json().get('data', []) or []
