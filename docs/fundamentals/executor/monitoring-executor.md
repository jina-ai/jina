(monitoring-executor)=
# Monitor

By default, every method which is decorated by the `@requests` decorator will be monitored, it will create a
[Prometheus Summary](https://prometheus.io/docs/concepts/metric_types/#summary) which will keep track of the time of 
the execution of the method.

This section documents the ability to add custom monitoring to the Executor with the Grafana/Prometheus.

Custom metrics are useful when you want to monitor each subpart of your Executors. Jina allows you to leverage
the full power of the [Prometheus Client](https://github.com/prometheus/client_python) to define useful metrics 
for each of your Executors. We provide a convenient wrapper as well, i.e `@monitor()`, which let you easily monitor
sub-method of your Executor. 

When the monitoring is enabled each Executor will expose its 
own metrics. This means that in practice each of the Executors will expose a Prometheus endpoint using the [Prometheus Client](https://github.com/prometheus/client_python).

```{admonition} Full detail on monitoring
:class: seealso
This section describes how to define and use **custom** metrics. To use the default metrics exposed by the Executor 
please refer to {ref}`this <monitoring-flow>` section.
```


## Define custom metrics

Sometimes monitoring the `encoding` method is not enough, you need to break it up into multiple parts that you want to 
monitor one by one.

It could be useful if your encoding phase is composed of two tasks: image processing and
image embedding. By using custom metrics on these two tasks you can identify potential bottlenecks.

Overall the ability to add custom metrics allows you to have the full flexibility on the monitoring of your Executor.

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


### Use `@monitor` decorator

Adding the custom monitoring on a method is as straightforward as decorating the method with `@monitor`.

```python
from jina import Executor, monitor


class MyExecutor(Executor):
    @monitor()
    def my_method(self):
        ...
```

This will create a [Prometheus summary](https://prometheus.io/docs/concepts/metric_types/#summary)
`jina_my_method_inference_seconds` which will keep track of the time of execution of `my_method

By default, the name and the documentation of the metric created by `@monitor` are auto-generated based on the name
of the function. However, you can name it by yourself by doing :

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
therefore because `@monitor` creates a [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) under the hood
your metrics name should finish with `seconds`
````

### Use Prometheus client

Under the hood, the monitoring feature of the Executor is handled by the 
Python [Prometheus-client](https://github.com/prometheus/client_python). The `@monitor` decorator is a convenient tool
to monitor sub-methods of an Executor, but you might need more flexibility and that is why you can access the Prometheus
client directly from the Executor to define every kind of metric supported by Prometheus.

Let's see it in an example


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

This will create a Prometheus [Counter](https://prometheus.io/docs/concepts/metric_types/#counter). 

````{admonition} Directly using the Prometheus client
:class: caution
You need to pass the metrics registry from the Executor when creating custom metrics directly with the Prometheus client.
````


## Example

Let's take an example to illustrate custom metrics:

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

The encode function is composed of two sub-functions.
* `preprocessing` which takes raw bytes from a DocumentArray and put them into a PyTorch tensor. 
* `model inference` calls the forward function of a deep learning model.

By default, only the `encode` function will be monitored. 

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
- {ref}`How to deploy and use the monitoring with Jina <monitoring>`
