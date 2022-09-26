import json
import multiprocessing
import time
from typing import Dict, Optional, Sequence, Tuple

import requests as req
from docarray import DocumentArray
from opentelemetry.context.context import Context
from opentelemetry.sdk.metrics._internal import MeterProvider
from opentelemetry.sdk.metrics._internal.export import (
    InMemoryMetricReader,
    MetricExporter,
    MetricExportResult,
    MetricReader,
)
from opentelemetry.sdk.metrics.export import MetricsData, PeriodicExportingMetricReader
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider, export
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.test.test_base import TestBase

from jina import Executor, Flow, requests


class ExecutorTestWithTracing(Executor):
    def __init__(
        self,
        metas: Optional[Dict] = None,
        requests: Optional[Dict] = None,
        runtime_args: Optional[Dict] = None,
        workspace: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(metas, requests, runtime_args, workspace, **kwargs)
        self.docs_counter = self.meter.create_counter(name='docs_counter')

    @requests(on='/index')
    def empty(self, docs: 'DocumentArray', otel_context: Context, **kwargs):
        with self.tracer.start_as_current_span('dummy', context=otel_context) as span:
            span.set_attribute('len_docs', len(docs))
            self.docs_counter.add(len(docs))
            return docs


class CustomSpanExporter(SpanExporter):
    """Implementation of :class:`.SpanExporter` that stores spans as json in a multiprocessing.list().

    This class can be used for testing purposes. It stores the exported spans
    in a list in memory that can be retrieved using the
    :func:`.get_finished_spans` method.
    """

    def __init__(self):
        self._mp_manager = multiprocessing.Manager()
        self._finished_spans = self._mp_manager.list()

    def clear(self):
        """Clear list of collected spans."""
        self._finished_spans[:] = []

    def get_finished_spans(self):
        """Get list of collected spans."""
        return tuple(self._finished_spans)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Stores a list of spans in memory."""
        for span in spans:
            self._finished_spans.append(span.to_json(indent=None))
        return SpanExportResult.SUCCESS


class CustomMetricExporter(MetricExporter):
    """Implementation of `MetricReader` that returns its metrics from :func:`get_metrics_data`.
    There are two internal data value holders from the multiprocessing library.
    The "self._collector" multiprocessing.Value type holds the latest metric export. This can be useful in some situations to check
    the latest export but it can be overwritten easily by another operation or metric provider reset.
    The "self._docs_count_data_points" holds the data points of a specific "docs_counter" metric.

    This is useful for e.g. unit tests.
    """

    def __init__(
        self,
    ):
        super().__init__()
        self._manager = multiprocessing.Manager()
        self._collector = self._manager.Value('s', '')
        self._docs_count_data_points = self._manager.list()

    def export(
        self,
        metrics_data: MetricsData,
        timeout_millis: float = 500,
        **kwargs,
    ) -> MetricExportResult:
        for resource_metrics in metrics_data.resource_metrics:
            for scope_metrics in resource_metrics.scope_metrics:
                for metric in scope_metrics.metrics:
                    if metric.name == 'docs_counter':
                        self._docs_count_data_points.append(
                            metric.data.to_json(indent=None)
                        )

        self._collector.value = metrics_data.to_json(indent=None)
        return MetricExportResult.SUCCESS

    def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
        pass

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        return True

    def get_metrics_data(self):
        return self._collector.value

    def get_docs_count_data_points(self):
        return self._docs_count_data_points


class TestHttpGatewayTracing(TestBase):
    custom_metric_exporter = CustomMetricExporter()

    def setUp(self):
        super().setUp()
        self.docs_input = {'data': [{'text': 'text_input'}]}

    def tearDown(self):
        super().tearDown()

    @staticmethod
    def create_tracer_provider(**kwargs):
        """Helper to create a configured tracer provider.

        Creates and configures a `TracerProvider` with a
        `SimpleSpanProcessor` and a `InMemorySpanExporter`.
        All the parameters passed are forwarded to the TracerProvider
        constructor.

        Returns:
            A list with the tracer provider in the first element and the
            in-memory span exporter in the second.
        """

        memory_exporter = CustomSpanExporter()

        tracer_provider = TracerProvider(**kwargs)
        span_processor = export.SimpleSpanProcessor(memory_exporter)
        tracer_provider.add_span_processor(span_processor)

        return tracer_provider, memory_exporter

    @staticmethod
    def create_meter_provider(
        **kwargs,
    ) -> Tuple[MeterProvider, MetricReader]:
        """Helper to create a configured meter provider
        Creates a `MeterProvider` and an `InMemoryMetricReader`.
        Returns:
            A tuple with the meter provider in the first element and the
            in-memory metrics exporter in the second
        """
        memory_reader = InMemoryMetricReader()
        custom_metric_reader = PeriodicExportingMetricReader(
            TestHttpGatewayTracing.custom_metric_exporter, export_interval_millis=500
        )

        metric_readers = kwargs.get("metric_readers", [])
        metric_readers.append(memory_reader)
        metric_readers.append(custom_metric_reader)
        kwargs["metric_readers"] = metric_readers
        meter_provider = MeterProvider(**kwargs)
        return meter_provider, memory_reader

    def partition_spans_by_kind(self):
        '''Returns three lists each containing spans of kind SpanKind.SERVER, SpanKind.CLIENT and SpandKind.INTERNAL'''
        server_spans = []
        client_spans = []
        internal_spans = []

        for span_json in self.memory_exporter.get_finished_spans():
            span = json.loads(span_json)
            span_kind = span.get('kind', '')
            if 'SpanKind.SERVER' == span_kind:
                server_spans.append(span)
            elif 'SpanKind.CLIENT' == span_kind:
                client_spans.append(span)
            elif 'SpanKind.INTERNAL' == span_kind:
                internal_spans.append(span)

        return (server_spans, client_spans, internal_spans)

    def test_http_span_attributes_default_args(self):
        f = Flow(protocol='http').add()

        with f:
            req.post(
                f'http://localhost:{f.port}/index',
                json=self.docs_input,
            )
            # give some time for the tracing and metrics exporters to finish exporting.
            time.sleep(1)

            self.assertEqual(0, len(self.get_finished_spans()))

    def test_http_span_attributes_with_executor(self):
        f = Flow(
            protocol='http', opentelemetry_tracing=True, opentelemetry_metrics=True
        ).add(uses=ExecutorTestWithTracing)

        with f:
            req.post(
                f'http://localhost:{f.port}/index',
                json=self.docs_input,
            )
            # give some time for the tracing and metrics exporters to finish exporting.
            time.sleep(1)

            (
                server_spans,
                client_spans,
                internal_spans,
            ) = self.partition_spans_by_kind()
            self.assertEqual(4, len(internal_spans))
            for internal_span in internal_spans:
                if internal_span.get('name', '') == 'dummy':
                    self.assertEqual(
                        len(self.docs_input), internal_span['attributes']['len_docs']
                    )

            self.assertEqual(5, len(server_spans))
            self.assertEqual(0, len(client_spans))
            self.assertEqual(9, len(self.get_finished_spans()))

            self.assertGreater(
                len(
                    TestHttpGatewayTracing.custom_metric_exporter.get_docs_count_data_points()
                ),
                0,
            )
