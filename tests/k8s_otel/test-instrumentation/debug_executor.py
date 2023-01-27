from typing import Optional

from opentelemetry.context.context import Context

from jina import DocumentArray, Executor, requests


class ExecutorTestWithTracing(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.meter:
            self.request_counter = self.meter.create_counter('request_counter')
        else:
            self.request_counter = None

    @requests
    def testing(
        self, docs: DocumentArray, tracing_context: Optional[Context], **kwargs
    ):
        if self.request_counter:
            self.request_counter.add(1)

        if self.tracer:
            with self.tracer.start_span('dummy', context=tracing_context) as span:
                span.set_attribute('len_docs', len(docs))
        return docs
