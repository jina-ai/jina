import time

import requests as req

from jina import Flow
from tests.unit.serve.runtimes.gateway import (
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
            (
                server_spans,
                client_spans,
                internal_spans,
            ) = self.partition_spans_by_kind()
            self.assertEqual(0, len(server_spans))
            # There are currently 4 SpanKind.CLIENT spans produced by the
            # a. /grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo (2)
            # b. /jina.JinaDiscoverEndpointsRPC/endpoint_discovery (1)
            # c. /jina.JinaSingleDataRequestRPC/process_single_data (1)
            # that cannot yet be completely disabled because the GrpcConnectionPool.get_grpc_channel
            # method is a static method. This means that until a concrete '.set_tracer_provider' gets executed, the tracer will
            # be a default ProxyTracerProvider.
            self.assertEqual(4, len(client_spans))
            self.assertEqual(0, len(internal_spans))
            self.assertEqual(4, len(self.get_finished_spans()))

    def test_http_span_attributes_with_executor(self):
        f = Flow(
            protocol='http', opentelemetry_tracing=True, opentelemetry_metrics=True
        ).add(uses=ExecutorTestWithTracing, name='executortest')

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

            # There are the usual 4 SpanKind.CLIENT spans as mentioned above.
            self.assertEqual(4, len(client_spans))
            # There are 5 total spans. The CLIENT spans from the above are being traced correctly by the server. Apart
            # from the spans mentioned in te above test, there is an extra span (expected) for the '/index'
            # request from the client that is handled by the gateway http server>
            self.assertEqual(5, len(server_spans))
            # The FASTApi app instrumentation tracks the server spans as SpanKind.INTERNAL. There are 4 spans for:
            # 1. /index http receive
            # 2. dummy operation in the Executor method
            # 3. /index http send
            # 4. /index http send
            self.assertEqual(4, len(internal_spans))
            self.assertEqual(13, len(self.get_finished_spans()))

            self.assertGreater(
                len(
                    TestHttpGatewayTracing.custom_metric_exporter.get_docs_count_data_points()
                ),
                0,
            )
