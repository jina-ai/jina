import multiprocessing
from typing import Dict, Optional, Sequence

from docarray import DocumentArray
from opentelemetry.context.context import Context
from opentelemetry.sdk.metrics._internal.export import (
    MetricExporter,
    MetricExportResult,
)
from opentelemetry.sdk.metrics.export import MetricsData
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from jina import Executor, requests


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
