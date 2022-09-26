import time

from jina import Client, Flow
from tests.unit.serve.runtimes.gateway import (
    ExecutorTestWithTracing,
    InstrumentationTestBase,
)


class TestGrpcGatewayTracing(InstrumentationTestBase):
    def setUp(self):
        super().setUp()
        self.docs_input = {'data': [{'text': 'text_input'}]}

    def tearDown(self):
        super().tearDown()

    def test_http_span_attributes_default_args(self):
        f = Flow(protocol='grpc').add()

        with f:
            c = Client(
                host=f'grpc://localhost:{f.port}',
            )
            c.post(
                f'/index',
                self.docs_input,
            )
            # give some time for the tracing and metrics exporters to finish exporting.
            time.sleep(1)

            self.assertEqual(5, len(self.get_finished_spans()))

    def test_http_span_attributes_with_executor(self):
        f = Flow(
            protocol='grpc', opentelemetry_tracing=True, opentelemetry_metrics=True
        ).add(uses=ExecutorTestWithTracing)

        with f:
            c = Client(
                host=f'grpc://localhost:{f.port}',
            )
            c.post(
                f'/index',
                self.docs_input,
            )
            # give some time for the tracing and metrics exporters to finish exporting.
            time.sleep(1)

            (
                server_spans,
                client_spans,
                internal_spans,
            ) = self.partition_spans_by_kind()
            self.assertEqual(1, len(internal_spans))
            for internal_span in internal_spans:
                if internal_span.get('name', '') == 'dummy':
                    self.assertEqual(
                        len(self.docs_input), internal_span['attributes']['len_docs']
                    )

            self.assertEqual(5, len(server_spans))
            self.assertEqual(5, len(client_spans))
            self.assertEqual(11, len(self.get_finished_spans()))

            self.assertGreater(
                len(
                    TestGrpcGatewayTracing.custom_metric_exporter.get_docs_count_data_points()
                ),
                0,
            )
