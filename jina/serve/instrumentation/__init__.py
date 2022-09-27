from opentelemetry import metrics, trace
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

    def __init__(self) -> None:
        self.tracer = trace.NoOpTracer()
        self.meter = metrics.NoOpMeter(name='no-op')

    def _setup_instrumentation(self) -> None:
        name = self.__class__.__name__
        if hasattr(self, 'name') and self.name:
            name = self.name

        if self.args.opentelemetry_tracing:
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource(attributes={SERVICE_NAME: name})
            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(
                JaegerExporter(
                    agent_host_name=self.args.jaeger_host,
                    agent_port=self.args.jaeger_port,
                )
            )
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(name)

        if self.args.opentelemetry_metrics:
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import (
                ConsoleMetricExporter,
                PeriodicExportingMetricReader,
            )
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource

            resource = Resource(attributes={SERVICE_NAME: name})

            metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
            meter_provider = MeterProvider(
                metric_readers=[metric_reader], resource=resource
            )
            metrics.set_meter_provider(meter_provider)
            self.meter = metrics.get_meter(name)

    def aio_tracing_server_interceptor(self):
        '''Create a gRPC aio server interceptor.
        :returns: A service-side aio interceptor object.
        '''
        from jina.serve.instrumentation._aio_server import (
            OpenTelemetryAioServerInterceptor,
        )

        return OpenTelemetryAioServerInterceptor(self.tracer)

    @staticmethod
    def aio_tracing_client_interceptors():
        '''Create a gRPC client aio channel interceptor.
        :returns: An invocation-side list of aio interceptor objects.
        '''
        tracer = trace.get_tracer(__name__)

        return [
            UnaryUnaryAioClientInterceptor(tracer),
            UnaryStreamAioClientInterceptor(tracer),
            StreamUnaryAioClientInterceptor(tracer),
            StreamStreamAioClientInterceptor(tracer),
        ]

    @staticmethod
    def tracing_client_interceptor():
        '''
        :returns: a gRPC client interceptor with the global tracing provider.
        '''
        return grpc_client_interceptor(trace.get_tracer_provider())
