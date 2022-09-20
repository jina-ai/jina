# These are the necessary import declarations
import os

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.grpc import (
    client_interceptor as grpc_client_interceptor,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

TRACER = trace.NoOpTracer
METER = metrics.NoOpMeter
resource = Resource(
    attributes={SERVICE_NAME: os.getenv('JINA_DEPLOYMENT_NAME', 'worker')}
)

if 'JINA_ENABLE_OTEL_TRACING' in os.environ:
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    TRACER = trace.get_tracer(os.getenv('JINA_DEPLOYMENT_NAME', 'worker'))
else:
    trace.set_tracer_provider(TRACER)

if 'JINA_ENABLE_OTEL_METRICS' in os.environ:
    metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
    metrics.set_meter_provider(meter_provider)
    # Sets the global meter provider
    METER = metrics.get_meter(os.getenv('JINA_DEPLOYMENT_NAME', 'worker'))
else:
    metrics.set_meter_provider(METER)


def client_tracing_interceptor():
    '''
    :returns: a gRPC client interceptor with the global tracing provider.
    '''
    return grpc_client_interceptor(trace.get_tracer_provider())
