import time

import requests as req

from jina import Flow
from tests.unit.serve.runtimes.gateway import (
    CustomMetricExporter,
    ExecutorTestWithTracing,
    InstrumentationTestBase,
)


class TestHttpGatewayTracing(InstrumentationTestBase):
    def setUp(self):
        super().setUp()
        self.docs_input = {'data': [{'text': 'text_input'}]}

    def tearDown(self):
        super().tearDown()

    def test_http_span_attributes_default_args(self):
        f = Flow(protocol='http').add()

        with f:
            req.post(
                f'http://localhost:{f.port}/index',
                json=self.docs_input,
            )
            # give some time for the tracing and metrics exporters to finish exporting.
            time.sleep(1)

            self.assertEqual(4, len(self.get_finished_spans()))

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
            self.assertEqual(4, len(client_spans))
            self.assertEqual(13, len(self.get_finished_spans()))

            self.assertGreater(
                len(
                    TestHttpGatewayTracing.custom_metric_exporter.get_docs_count_data_points()
                ),
                0,
            )
