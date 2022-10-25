(monitoring-executor)=
# Monitor

```{admonition} Deprecated
:class: caution
The Prometheus-only feature will soon be deprecated in favor of the OpenTelemetry API. Refer to {ref}`Executor Instrumentation <instrumenting-executor>` and {ref}`Flow Instrumentation <instrumenting-flow>` for the current methods for observing and instrumenting Jina.
```

By default, every method decorated by the {class}`~jina.requests` decorator is monitored and creates a
[Prometheus Summary](https://prometheus.io/docs/concepts/metric_types/#summary) which tracks the execution time of 
the method.

This section documents the ability to add custom monitoring to the {class}`~jina.Executor` with Grafana/Prometheus.

Custom metrics are useful when you want to monitor each subpart of your Executors. Jina lets you leverage
the [Prometheus Client](https://github.com/prometheus/client_python) to define useful metrics 
for each of your Executors. We provide a convenient wrapper as well, i.e {func}`~jina.monitor`, which lets easily monitor
your Executor's sub-methods. 

When monitoring is enabled, each Executor exposes its 
own metrics. This means that in practice each Executor exposes a Prometheus endpoint using the [Prometheus Client](https://github.com/prometheus/client_python).

```{hint}
Depending on your deployment type (local, Kubernetes or JCloud), you need to ensure a running Prometheus/Grafana stack.
Check the {ref}`Flow and monitoring stack deployment section <deploy-flow-monitoring>` to find out how to provision 
your monitoring stack.
```

```{admonition} Full detail on monitoring
:class: seealso
This section describes how to define and use **custom** metrics. To use the Executor's default metrics, refer to {ref}`the Flow monitoring <monitoring-flow>` section.
```


## Define custom metrics

Sometimes monitoring the `encoding` method is not enough - you need to break it up into multiple parts that you want to 
monitor one by one.

This is useful if your encoding phase is composed of two tasks: image processing and
image embedding. By using custom metrics on these two tasks you can identify potential bottlenecks.

Overall adding custom metrics gives you full flexibility when monitoring your Executor.

### Use context manager

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


### Use the `@monitor` decorator

Adding custom monitoring to a method can be done by decorating the method with {func}`~jina.monitor`.

```python
from jina import Executor, monitor


class MyExecutor(Executor):
    @monitor()
    def my_method(self):
        ...
```

This creates a [Prometheus summary](https://prometheus.io/docs/concepts/metric_types/#summary)
`jina_my_method_inference_seconds` which tracks the execution time of `my_method`

By default, the name and documentation of the metric created by {func}`~jina.monitor` are auto-generated based on the function's name. 
However, you can name it by yourself:

```python
@monitor(
    name='my_custom_metrics_seconds', documentation='This is my custom documentation'
)
def method(self):
    ...
```

````{admonition} respect Prometheus naming
:class: caution
You should respect Prometheus naming [conventions](https://prometheus.io/docs/practices/naming/#metric-names). 
Because {func}`~jina.monitor` creates a [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) under the hood
your metrics name should end with `seconds`
````

### Use Prometheus client

Under the hood, the Executor's monitoring feature is handled by the 
Python [Prometheus-client](https://github.com/prometheus/client_python). The {func}`~jina.monitor` decorator is a convenient tool
to monitor sub-methods of an Executor, but you might need more flexibility. In that case can access the Prometheus
client directly from the Executor to define any kind of metric supported by Prometheus.

Let's see it in an example:


```python
from jina import requests, Executor, DocumentArray

from prometheus_client import Counter


class MyExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = Counter(
            name='my_count_total',
            documentation='my count',
            registry=self.runtime_args.metrics_registry,
        )

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        self.counter.inc(len(docs))
```

This creates a Prometheus [Counter](https://prometheus.io/docs/concepts/metric_types/#counter). 

````{admonition} Directly using the Prometheus client
:class: caution
You need to pass the metrics registry from the Executor when creating custom metrics directly with the Prometheus client.
````


## Example

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

- {ref}`List of available metrics <monitoring-flow>`
- {ref}`How to deploy and use monitoring in Jina <monitoring>`
