import json
import time
from typing import Tuple

import requests as req
from opentelemetry.sdk.metrics._internal import MeterProvider
from opentelemetry.sdk.metrics._internal.export import (
    InMemoryMetricReader,
    MetricReader,
)
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider, export
from opentelemetry.test.test_base import TestBase

from jina import Flow
from tests.unit.serve.runtimes.gateway import (
    CustomMetricExporter,
    CustomSpanExporter,
    ExecutorTestWithTracing,
)


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
