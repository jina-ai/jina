(monitoring-executor)=
# Monitor Executor with Custom Metrics

Jina allow you to monitor every part of a Flow, including Executor, with the Grafana/Prometheus.
This section document the ability to add custom monitoring to the Executor.

```{admonition} Full detail on monitoring
:class: seealso
More details on the monitoring {ref}`here <monitoring-flow>`
```

When the monitoring is enabled each Executor will expose its 
own metrics. It means that in practice each of the Executor will expose a Prometheus endpoint using the [prometheus-client](https://github.com/prometheus/client_python).

By default, every method which is decorated by the `@request` decorator will be monitored

````{admonition} Only use this feature to do custom monitoring
:class: caution
This section describe how to do define and use **custom** metrics. To use the default metrics expose by the Executor 
please refer to {ref}`this <monitoring-flow>` section.
````

## Defining custom metrics

Sometime monitoring the `enconding` method is not enough, you need to break it up into multiple parts that you want to 
monitor one by one.

It could be useful if your encoding phase for example is composed of two tasks: image processing and
image embedding. By using custom metrics on this two tasks you could identify potential bottleneck.

Overall the ability to add custom metrics allows you to have the full flexibility on the monitoring of your Executor.

### Defining custom metrics with `@monitor`

Let's take an example to illustrate the custom metrics

```python
from jina import requests, Executor
from docarray import DocumentArray


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

This Executor encodes is composed of two sub function.
* `preprocessing` which take raw bytes from a DocumentArray and put it into a torch tensor. 
* `model inference` call the forward function of a deep learning model.

By default, only the encode function will be monitored. 

````{admonition} Using @monitor
:class: hint
Adding the custom monitoring on a method is as straightforward as decorating the method with `@monitor` 
````

```{code-block} python
---
emphasize-lines: 6, 10
---
from jina import requests,monitor,Executor
from docarray import DocumentArray

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

This will create two [Prometheus summaries](https://prometheus.io/docs/concepts/metric_types/#summary)
`jina_model_inference_seconds`and `jina_preprocessing_seconds` which will keep track of the time of execution of these
methods.

By default, the name and the documentation of the metric created by `@monitor` are auto generated based on the name
of the function. However, you can precise it by yourself by doing :
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
therefore because `@monitor` create a [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) under the hood
your metrics name should finish with `seconds`
````

### Defining custom metrics directly with the Prometheus client

Under the hood the monitoring feature of the Executor is handled by the 
python [Prometheus-client](https://github.com/prometheus/client_python). The `@monitor` decorator is a convenient tool
to monitor sub method of an Executor, but you might need more flexibility and that is why you can access the Prometheus
client directly from the executor to define every kind of metrics supported by Prometheus.

let's see it in an example

```python
from jina import requests, Executor
from docarray import DocumentArray

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


## See further

- {ref}`List of available metrics <monitoring-flow>`
- {ref}`How to deploy and use the monitoring with Jina <monitoring>`
