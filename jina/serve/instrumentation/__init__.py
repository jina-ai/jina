from typing import Optional

from opentelemetry import metrics as opentelmetry_metrics
from opentelemetry import trace
from opentelemetry.instrumentation.grpc import (
    client_interceptor as grpc_client_interceptor,
)

from jina.serve.instrumentation._aio_client import (
    StreamStreamAioClientInterceptor,
    StreamUnaryAioClientInterceptor,
    UnaryStreamAioClientInterceptor,
    UnaryUnaryAioClientInterceptor,
)


class InstrumentationMixin:
    '''Instrumentation mixin for OpenTelemetery Tracing and Metrics handling'''

    def _setup_instrumentation(
        self,
        name: str,
        tracing: Optional[bool] = False,
        span_exporter_host: Optional[str] = '0.0.0.0',
        span_exporter_port: Optional[int] = 6831,
        metrics: Optional[bool] = False,
        metrics_exporter_host: Optional[str] = '0.0.0.0',
        metrics_exporter_port: Optional[int] = 6831,
    ) -> None:

        self.tracing = tracing
        self.metrics = metrics

        if tracing:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource(attributes={SERVICE_NAME: name})
            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=f'{span_exporter_host}:{span_exporter_port}', insecure=True
                )
            )
            provider.add_span_processor(processor)
            self.tracer_provider = provider
            self.tracer = provider.get_tracer(name)
        else:
            self.tracer_provider = trace.NoOpTracerProvider()
            self.tracer = trace.NoOpTracer()

        if metrics:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource

            resource = Resource(attributes={SERVICE_NAME: name})

            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=f'{metrics_exporter_host}:{metrics_exporter_port}',
                    insecure=True,
                )
            )
            meter_provider = MeterProvider(
                metric_readers=[metric_reader], resource=resource
            )
            self.meter_provider = meter_provider
            self.meter = self.meter_provider.get_meter(name)
        else:
            self.meter_provider = opentelmetry_metrics.NoOpMeterProvider()
            self.meter = opentelmetry_metrics.NoOpMeter(name='no-op')

    def aio_tracing_server_interceptor(self):
        '''Create a gRPC aio server interceptor.
        :returns: A service-side aio interceptor object.
        '''
        if self.tracing:
            from jina.serve.instrumentation._aio_server import (
                OpenTelemetryAioServerInterceptor,
            )

            return [OpenTelemetryAioServerInterceptor(self.tracer)]
        else:
            return None

    @staticmethod
    def aio_tracing_client_interceptors(
        tracer: Optional[trace.Tracer] = trace.NoOpTracer(),
    ):
        '''Create a gRPC client aio channel interceptor.
        :param tracer: Optional tracer that is used to instrument the client interceptors. If absent, a NoOpTracer will be used.
        :returns: An invocation-side list of aio interceptor objects.
        '''
        if not tracer:
            tracer = trace.NoOpTracer()

        return [
            UnaryUnaryAioClientInterceptor(tracer),
            UnaryStreamAioClientInterceptor(tracer),
            StreamUnaryAioClientInterceptor(tracer),
            StreamStreamAioClientInterceptor(tracer),
        ]

    @staticmethod
    def tracing_client_interceptor(
        tracer_provider: Optional[trace.TracerProvider] = trace.NoOpTracerProvider(),
    ):
        '''
        :param tracer_provider: Optional tracer provider that is used to instrument the client interceptor. If absent, a NoOpTracer provider will be used.
        :returns: a gRPC client interceptor with the global tracing provider.
        '''
        if not tracer_provider:
            tracer_provider = trace.NoOpTracerProvider()
        return grpc_client_interceptor(tracer_provider)
