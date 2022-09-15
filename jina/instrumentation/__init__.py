# These are the necessary import declarations
import os

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

TRACER = trace.NoOpTracer
if 'JINA_ENABLE_OTEL_TRACING':
    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    TRACER = trace.get_tracer(os.getenv('JINA_DEPLOYMENT_NAME', 'worker'))

metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
meter_provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
# Sets the global meter provider
METER = metrics.get_meter(os.getenv('JINA_DEPLOYMENT_NAME', 'worker'))
