import functools
from timeit import default_timer
from typing import TYPE_CHECKING, Dict, Optional, Sequence

if TYPE_CHECKING: # pragma: no cover
    from grpc.aio._interceptor import ClientInterceptor, ServerInterceptor
    from opentelemetry.instrumentation.grpc._client import (
        OpenTelemetryClientInterceptor,
    )
    from opentelemetry.metrics import Histogram
    from prometheus_client import Summary


class InstrumentationMixin:
    '''Instrumentation mixin for OpenTelemetery Tracing and Metrics handling'''

    def _setup_instrumentation(
        self,
        name: str,
        tracing: Optional[bool] = False,
        traces_exporter_host: Optional[str] = '0.0.0.0',
        traces_exporter_port: Optional[int] = 6831,
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
                    endpoint=f'{traces_exporter_host}:{traces_exporter_port}',
                    insecure=True,
                )
            )
            provider.add_span_processor(processor)
            self.tracer_provider = provider
            self.tracer = provider.get_tracer(name)
        else:
            self.tracer_provider = None
            self.tracer = None

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
            self.meter_provider = None
            self.meter = None

    def aio_tracing_server_interceptors(
        self,
    ) -> Optional[Sequence['ServerInterceptor']]:
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

    def aio_tracing_client_interceptors(
        self,
    ) -> Optional[Sequence['ClientInterceptor']]:
        '''Create a gRPC client aio channel interceptor.
        :returns: An invocation-side list of aio interceptor objects.
        '''

        if self.tracing:
            from jina.serve.instrumentation._aio_client import (
                StreamStreamAioClientInterceptor,
                StreamUnaryAioClientInterceptor,
                UnaryStreamAioClientInterceptor,
                UnaryUnaryAioClientInterceptor,
            )

            return [
                UnaryUnaryAioClientInterceptor(self.tracer),
                UnaryStreamAioClientInterceptor(self.tracer),
                StreamUnaryAioClientInterceptor(self.tracer),
                StreamStreamAioClientInterceptor(self.tracer),
            ]
        else:
            return None

    def tracing_client_interceptor(self) -> Optional['OpenTelemetryClientInterceptor']:
        '''
        :returns: a gRPC client interceptor with the global tracing provider.
        '''
        if self.tracing:
            from opentelemetry.instrumentation.grpc import (
                client_interceptor as grpc_client_interceptor,
            )

            return grpc_client_interceptor(self.tracer_provider)
        else:
            return None


class MetricsTimer:
    '''Helper dataclass that accepts optional Summary or Histogram recorders which are used to record the time take to execute
    the decorated or context managed function
    '''

    def __init__(
        self,
        summary_metric: Optional['Summary'],
        histogram: Optional['Histogram'],
        histogram_metric_labels: Dict[str, str] = {},
    ) -> None:
        self._summary_metric = summary_metric
        self._histogram = histogram
        self._histogram_metric_labels = histogram_metric_labels

    def _new_timer(self):
        return self.__class__(self._summary_metric, self._histogram)

    def __enter__(self):
        self._start = default_timer()
        return self

    def __exit__(self, *exc):
        duration = max(default_timer() - self._start, 0)
        if self._summary_metric:
            self._summary_metric.observe(duration)
        if self._histogram:
            self._histogram.record(duration, attributes=self._histogram_metric_labels)

    def __call__(self, f):
        '''function that gets called when this class is used as a decortor
        :param f: function that is decorated
        :return: wrapped function
        '''

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Obtaining new instance of timer every time
            # ensures thread safety and reentrancy.
            with self._new_timer():
                return f(*args, **kwargs)

        return wrapped
