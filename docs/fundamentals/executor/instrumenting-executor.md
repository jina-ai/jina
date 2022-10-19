(instrumenting-executor)=
# Instrumentation

Instrumentation consists of [OpenTelemetry](https://opentelemetry.io) Tracing and Metrics. Both features can be enabled independently and allows you to collect various request level and application level metrics for anaylizing the real time behavior of your Executor. 

This section documents the ability to create custom traces and metrics apart from the default ones.

```{admonition} Full detail on Instrumentation
:class: seealso
This section describes how to use **custom** tracing spans. To use the Executor's default tracing, refer to {ref}`the Flow Instrumentation <instrumenting-flow>` section.
```

```{hint}
The OpenTelemetry collector backend setup is described in the {ref}`OpenTelemetry Setup <opentelemetry>` section.
```

## Tracing

Every method that is decorated using the {class}`~jina.requests` decorator adds a 
default tracing span for the defined operation. In addition the operation span context 
is propagated to the method for creating further user defined child spans within the 
method.

Custom spans can be created to observe the operation individual steps or record various details and attributes with a finer granularity. When tracing is enabled, Jina provides the OpenTelemetry Tracer implementation as an Executor class attribute that can be used to create new child spans. The `tracing_context` method argument contains the parent span context using which a new span can be created to trace the desired operation in the method.

If tracing is enabled, each executor exports its traces to the configured exporter host via the [Span Exporter](https://opentelemetry.io/docs/reference/specification/trace/sdk/#span-exporter) which are combined by the backend for visualization and alerting purposes.


### Create custom traces

A `request` method is the public method used to expose the operation as an API. Depending on the complexity, the method can often be composed of different sub operations that is required to build the final response. 

Each internal step along with its global or request specific attributes can be recorded/observed giving a more finer grained view of the operation at the request level. This helps to quickly identify bottlenecks and isolate request patterns that are causing service degradation or errors.

The `self.tracer` class attribute can be used to create a new child span using the `tracing_context` method argument as follows:

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, tracing_context, **kwargs):
        with self.tracer.start_as_current_span(
            'process_docs', context=tracing_context
        ) as process_span:
            process_span.set_attribute('sampling_rate', 0.01)
            docs = process(docs)
            with self.tracer.start_as_current_span('update_docs') as update_span:
                try:
                    update_span.set_attribute('len_updated_docs', len(docs))
                    docs = update(docs)
                except Exception as ex:
                    update_span.set_status(Status(StatusCode.ERROR))
                    update_span.record_exception(ex)
```

The above pieces of instrumentation generate 3 spans:
 1. Default span with name `foo` for the overall method.
 2. `process_span` that measures the `process` and `update` sub operations along with a `sampling_rate` attribute that might be a constant or specific to the request/operation.
 3. `update_span` that measures the `updated` operation along with any exception that might arise during the operation. The exception is recorded and marked on the `update_span` span. Since the exception is swallowed, the request succeeds with successful parent spans.


```{admonition} 
The python OpenTelemetry API provides a global tracer via the `opentelemetry.trace.tracer` method which is not set or used directly in any Jina implementated functionality. The class attribute `self.tracer` is used for the default `@requests` method tracing and it must also be used as much as possible within the method for creating child spans.

However within a span context, the `opentelemetry.trace.get_current_span()` method will return the span created inside the context.
```

````{admonition} respect OpenTelemetry Tracing semantic conventions
:class: caution
You should respect OpenTelemetry Tracing [semantic conventions](https://opentelemetry.io/docs/reference/specification/trace/semantic_conventions/).
````

````{hint}
If tracing is not enabled by default or enabled per environment basis, its a good practice to check for the existence of the `self.tracer` before usage. If metrics is disabled then `self.tracer` will be None.
````

## Metrics

By default, every method decorated by the {class}`~jina.requests` decorator is monitored and creates a
[Histogram](https://opentelemetry.io/docs/reference/specification/metrics/data-model/#histogram) which tracks the execution time of 
the method.

This section documents the ability to add custom monitoring to the {class}`~jina.Executor` with OpenTelemetry Metrics API.

Custom metrics are useful when you want to monitor each subpart of your Executors. Jina lets you leverage
the [Meter](https://opentelemetry.io/docs/reference/specification/metrics/api/#meter) to define useful metrics 
for each of your Executors. We provide a convenient wrapper as well, i.e {func}`~jina.monitor`, which lets easily monitor
your Executor's sub-methods. 

When metrics is enabled, each Executor exposes its 
own metrics via the [Metric Exporter](https://opentelemetry.io/docs/reference/specification/metrics/sdk/#metricexporter).


### Define custom metrics

Sometimes monitoring the `encoding` method is not enough - you need to break it up into multiple parts that you want to monitor one by one.

This is useful if your encoding phase is composed of two tasks: image processing and
image embedding. By using custom metrics on these two tasks you can identify potential bottlenecks.

Overall adding custom metrics gives you full flexibility when monitoring your Executor.

#### Use context manager

You can use `self.monitor` to monitor the internal blocks of your function:

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        with self.monitor('processing_seconds', 'Time processing my document'):
            docs = process(docs)
        print(docs.texts)
        with self.monitor('update_seconds', 'Time updates my document'):
            docs = update(docs)
```


#### Use the `@monitor` decorator

Adding custom monitoring to a method can be done by decorating the method with {func}`~jina.monitor`.

```python
from jina import Executor, monitor


class MyExecutor(Executor):
    @monitor()
    def my_method(self):
        ...
```

This creates a [Histogram](https://opentelemetry.io/docs/reference/specification/metrics/data-model/#histogram) `jina_my_method_seconds` which tracks the execution time of `my_method`

By default, the name and documentation of the metric created by {func}`~jina.monitor` are auto-generated based on the function's name. 
However, you can name it by yourself:

```python
@monitor(
    name='my_custom_metrics_seconds', documentation='This is my custom documentation'
)
def method(self):
    ...
```

````{admonition} respect OpenTelemetry Metrics semantic conventions
:class: caution
You should respect OpenTelemetry Metrics [semantic conventions](https://opentelemetry.io/docs/reference/specification/metrics/semantic_conventions/).
````

#### Use OpenTelemetry Meter

Under the hood, the Executor's metrics feature is handled by the 
Python [OpenTelemetry Metrics API](https://opentelemetry.io/docs/concepts/signals/metrics/). The {func}`~jina.monitor` decorator is a convenient tool
to monitor sub-methods of an Executor, but you might need more flexibility. In that case can use the `self.meter` Executor class attribute to create supported instruments.

Let's see it in an example:


```python
from jina import requests, Executor, DocumentArray

from prometheus_client import Counter


class MyExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = self.meter.create_counter('my_count', 'my count')

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        self.counter.inc(len(docs))
```

This creates a [Counter](https://opentelemetry.io/docs/reference/specification/metrics/api/#counter) that can be used to incrementally tracks the number of doucments recevied in each request. 

````{hint}
If metrics is not enabled by default or enabled per environment basis, its a good practice to check for the existence of the `self.meter` and the `self.counter` before usage. If metrics is disabled then `self.meter` will be None.
````


#### Example

Let's use an example to show custom metrics:

```python
from jina import requests, Executor, DocumentArray


class MyExecutor(Executor):
    def preprocessing(self, docs: DocumentArray):
        ...

    def model_inference(self, tensor):
        ...

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        docs.tensors = self.preprocessing(docs)
        docs.embedding = self.model_inference(docs.tensors)
```

The `encode` function is composed of two sub-functions.
* `preprocessing` takes raw bytes from a DocumentArray and puts them into a PyTorch tensor. 
* `model inference` calls the forward function of a deep learning model.

By default, only the `encode` function is monitored:

````{tab} Decorator
```{code-block} python
---
emphasize-lines: 5, 9
---
from jina import requests, monitor, Executor, DocumentArray

class MyExecutor(Executor):

    @monitor()
    def preprocessing(self, docs: DocumentArray):
        ...

    @monitor()
    def model_inference(self, tensor):
        ...

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        docs.tensors = self.preprocessing(docs)
        docs.embedding = self.model_inference(docs.tensors)
```
````

````{tab} Context manager

```{code-block} python
---
emphasize-lines: 13, 15
---
from jina import requests, Executor, DocumentArray

def preprocessing(self, docs: DocumentArray):
    ...

def model_inference(self, tensor):
    ...

class MyExecutor(Executor):

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        with self.monitor('preprocessing_seconds', 'Time preprocessing the requests'):
            docs.tensors = preprocessing(docs)
        with self.monitor('model_inference_seconds', 'Time doing inference the requests'):
            docs.embedding = model_inference(docs.tensors)
```
````

## See further

- {ref}`List of available metrics <instrumenting-flow>`
- {ref}`How to deploy and use OpenTelemetry in Jina <opentelemetry>`
- [Tracing in OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/traces/)
- [Metrics in OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/metrics/)
