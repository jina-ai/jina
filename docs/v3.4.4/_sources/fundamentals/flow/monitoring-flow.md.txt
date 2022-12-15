(monitoring-flow)=
# Monitor Flow
 
A Jina {ref}`Flow <flow-cookbook>` exposes several core metrics that allow you to have a deeper look
at what is happening inside it. Metrics allow you to, for example, monitor the overall performance 
of your Flow, detect bottlenecks, or alert your team when some component of your Flow is down.

Jina Flows expose metrics in the [Prometheus format](https://prometheus.io/docs/instrumenting/exposition_formats/). This is a plain text format that is understandable by both humans and machines. These metrics are intended to be scraped by
[Prometheus](https://prometheus.io/), an industry-standard tool for collecting and monitoring metrics.

To visualize your metrics through a dashboard, we recommend [Grafana](https://grafana.com/)


## Enable the monitoring in a Flow

A {ref}`Flow <flow-cookbook>` is composed of several Pods, namely the Gateway, the Executors, and potentially a Head (see the {ref}`architecture overview <architecture-overview>` for more details). Each of these Pods is its own microservice. These services expose their own metrics using the [Prometheus client](https://prometheus.io/docs/instrumenting/clientlibs/).
This means that they are as many metrics endpoints as there are Pods in your Flow. 

Let's give an example to illustrate it :

````{tab} via Python API

This example shows how to start a Flow with monitoring enabled via the Python API:

```python
from jina import Flow

with Flow(monitoring=True, port_monitoring=9090).add(
    uses='jinahub://SimpleIndexer', port_monitoring=9091
) as f:
    f.block()
```
````

````{tab} via YAML
This example shows how to start a Flow with monitoring enabled via yaml:

In a `flow.yaml` file
```yaml
jtype: Flow
with:
  monitoring: true
  port_monitoring: 9090
executors:
- uses: jinahub://SimpleIndexer
  port_monitoring: 9091
```

```bash
jina flow --uses flow.yaml
```
````

This Flow will create two Pods, one for the Gateway, and one for the SimpleIndexer Executor, therefore it will create two 
metrics endpoints:

* `http://localhost:9090  ` for the gateway
* `http://localhost:9091  ` for the SimpleIndexer

````{admonition} Default Monitoring port
:class: hint
The default monitoring port is `9090`, if you want to enable the monitoring on both the Gateway and the Executors you need to specify
the `prometheus_port` for the Executors. 
````


Because each Pod in a Flow exposes its own metrics, the monitoring feature can be used independently on each Pod.
This means that you are not forced to always monitor every Pod of your Flow. For example, you could be only interested in
metrics coming from the Gateway, and therefore you only activate the monitoring on it. On the other hand, you might be only
interested in monitoring a single Executor. Note that by default the monitoring is disabled everywhere.

To enable the monitoring you need to pass `monitoring = True` when creating the Flow.
```python
Flow(monitoring=True).add(...)
```

````{admonition} Enabling Flow
:class: hint
Passing `monitoring = True` when creating the Flow will enable the monitoring on **all the Pods** of your Flow. 
````

If you want to enable the monitoring only on the Gateway, you need to first enable the feature for the entire Flow, and then disable it for the Executor which you are not interested in.

```python
Flow(monitoring=True).add(monitoring=False, ...).add(monitoring=False, ...)
```

On the other hand, If you want to only enable the monitoring on a given Executor you should do:
```python
Flow().add(...).add(uses=MyExecutor, monitoring=True)
```

## Available metrics

Flows support different metrics out of the box, in addition to allowing the user to define their own custom metrics.

Because not all Pods have the same role, they expose different kinds of metrics:



### Gateway Pods

| Metrics name                       | Metrics type                                                         | Description                                                                                                                                                                                                                                                                |
|------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds`   | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measures the time elapsed between receiving a request from the client and sending back the response.                                                                                                                                                                    |
| `jina_sending_request_seconds`     | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measures the time elapsed between sending a downstream request to an Executor/Head and receiving the response back.                                                                                                                                                         |

```{seealso} 
You can find more information on the different type of metrics in Prometheus [here](https://prometheus.io/docs/concepts/metric_types/#metric-types)
```

### Head Pods

| Metrics name                       | Metrics type                                                          | Description                                                                                                     |
|------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds`   | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)  | Measure the time elapsed between receiving a request from the gateway and sending back the response.        |
| `jina_sending_request_seconds`     | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)  | Measure the time elapsed between sending a downstream request to an Executor and receiving the response back.   |

### Executor Pods

| Metrics name                     | Metrics type                                                         | Description                                                                                                           |
|----------------------------------|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds` | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measure the time elapsed between receiving a request from the gateway (or the head) and sending back the response. |
| `jina_process_request_seconds`   | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measure the time spend calling the requested method                                                                   |
| `jina_document_processed_total`  | [Counter](https://prometheus.io/docs/concepts/metric_types/#counter) | Counts the number of Documents processed by an Executor                                                                 |

```{seealso} 
Beyond monitoring every endpoint of an Executor you can define {ref}`custom metrics <monitoring-executor>`for you 
Executor. 
```

```{hint} 
 `jina_receiving_request_seconds` is different from `jina_process_request_seconds` because it includes the gRPC communication overhead whereas `jina_process_request_seconds` is only about the time spend calling the function 
```

## See further

- {ref}`Defining custom metrics in an Executor <monitoring-executor>`
- {ref}`How to deploy and use the monitoring with Jina <monitoring>`
- [Using Grafana to visualize Prometheus metrics](https://grafana.com/docs/grafana/latest/getting-started/getting-started-prometheus/)
