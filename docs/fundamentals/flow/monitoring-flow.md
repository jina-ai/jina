(monitoring-flow)=
# Monitor
 
A Jina {class}`~jina.Flow` exposes several core metrics that allow you to have a deeper look
at what is happening inside it. Metrics allow you to, for example, monitor the overall performance 
of your Flow, detect bottlenecks, or alert your team when some component of your Flow is down.

Jina Flows expose metrics in the [Prometheus format](https://prometheus.io/docs/instrumenting/exposition_formats/). This is a plain text format that is understandable by both humans and machines. These metrics are intended to be scraped by
[Prometheus](https://prometheus.io/), an industry-standard tool for collecting and monitoring metrics.

To visualize your metrics through a dashboard, we recommend [Grafana](https://grafana.com/).

```{hint}
Depending on your deployment type (local, Kubernetes or JCloud), you need to ensure a running Prometheus/Grafana stack.
Check the {ref}`Flow and monitoring stack deployment section <deploy-flow-monitoring>` to find out how to provision 
your monitoring stack.
```

## Enable monitoring

A {class}`~jina.Flow` is composed of several Pods, namely the {class}`~jina.serve.runtimes.gateway.GatewayRuntime`, the {class}`~jina.Executor`s, and potentially a {class}`~jina.serve.runtimes.head.HeadRuntime` (see the {ref}`architecture overview <architecture-overview>` for more details). Each of these Pods is its own microservice. These services expose their own metrics using the [Prometheus client](https://prometheus.io/docs/instrumenting/clientlibs/).
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

* `http://localhost:9090` for the gateway
* `http://localhost:9091` for the SimpleIndexer

````{admonition} Change the default monitoring port
:class: caution
When Jina is used locally, all of the `port_monitoring` will be random by default (within the range [49152, 65535]). However we 
strongly encourage you to precise these ports for the Gateway and for all of the Executors. Otherwise it will change at 
restart and you will have to change your Prometheus configuration file.
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

### Enable monitoring with replicas and shards

```{tip} 
This section is only relevant if you deploy your Flow natively. When deploying your Flow with Kubernetes or Docker Compose
all of the `port_monitoring` will be set to default : `9090`.  
```

To enable monitoring with replicas and shards when deploying natively, you need to pass a list of `port_monitoring` separated by a comma to your Flow.

Example:

````{tab} via Python API

```python
from jina import Flow

with Flow(monitoring=True).add(
    uses='jinahub://SimpleIndexer', replicas=2, port_monitoring='9091,9092'
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
executors:
- uses: jinahub://SimpleIndexer
  replicas=2
  port_monitoring: '9091,9092'
```

```bash
jina flow --uses flow.yaml
```
````

```{tip} Monitoring with shards
When using shards, an extra head will be created and you will need to pass a list of N+1 ports to `port_monitoring`, N beeing the number of shards you desire
```

If you precise fewer `port_monitoring` than you have replicas of your Executor (or even not passing any at all), the unknown ports
will be assigned randomly. It is a better practice to precise a port for every replica, otherwise you will have to change 
your Prometheus configuration each time you restart your application.

## Available metrics

A {class}`~jina.Flow` supports different metrics out of the box, in addition to allowing the user to define their own custom metrics.

Because not all Pods have the same role, they expose different kinds of metrics:



### Gateway Pods

| Metrics name                        | Metrics type                                                           | Description                                                                                                        |
|-------------------------------------|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds`    | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)   | Measures the time elapsed between receiving a request from the client and sending back the response.               |
| `jina_sending_request_seconds`      | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)   | Measures the time elapsed between sending a downstream request to an Executor/Head and receiving the response back. |
| `jina_number_of_pending_requests`   | [Gauge](https://prometheus.io/docs/concepts/metric_types/#gauge)       | Counts the number of pending requests                                                                              |
| `jina_successful_requests_total`    | [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)   | Counts the number of successful requests returned by the gateway                                                   |
| `jina_failed_requests_total`        | [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)   | Counts the number of failed requests returned by the gateway                                                       |
| `jina_sent_request_bytes`           | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)   | Measures the size in bytes of the request sent by the Gateway to the Executor or the Head                    |
| `jina_received_response_bytes`         | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)   | Measures the size in bytes of the request returned by the Executor                                           |
| `jina_received_request_bytes`           | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)   | Measures the size of the request in bytes received at the Gateway level                                            |
| `jina_sent_response_bytes`  | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)   | Measures the size in bytes of the response returned from the Gateway to the Client                                    |

```{seealso} 
You can find more information on the different type of metrics in Prometheus [here](https://prometheus.io/docs/concepts/metric_types/#metric-types)
```

### Head Pods

| Metrics name                            | Metrics type                                                            | Description                                                                                                   |
|-----------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds`        | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)    | Measures the time elapsed between receiving a request from the gateway and sending back the response.          |
| `jina_sending_request_seconds`          | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)    | Measures the time elapsed between sending a downstream request to an Executor and receiving the response back. |
| `jina_sending_request_bytes`            | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)    | Measures the size of the downstream requests send to an Executor in bytes                                      |
| `jina_failed_requests_total`            | [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)    | Counts the number of failed requests returned by the gateway                                                  |
| `jina_sent_request_bytes`               | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)    | Measures the size in bytes of the request sent by the Head to the Executor                              |
| `jina_received_response_bytes`             | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)    | Measures the size in bytes of the response returned by the Executor                                      |

### Executor Pods

| Metrics name                     | Metrics type                                                         | Description                                                                                                 |
|----------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds` | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measures the time elapsed between receiving a request from the gateway (or the head) and sending back the response. |
| `jina_process_request_seconds`   | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measures the time spend calling the requested method                                                         |
| `jina_document_processed_total`  | [Counter](https://prometheus.io/docs/concepts/metric_types/#counter) | Counts the number of Documents processed by an Executor                                                     |
| `jina_successful_requests_total` | [Counter](https://prometheus.io/docs/concepts/metric_types/#counter) | Total count of successful requests returned by the Executor across all endpoints                            |
| `jina_failed_requests_total`     | [Counter](https://prometheus.io/docs/concepts/metric_types/#counter) | Total count of failed requests returned by the Executor across all endpoints                                |
| `jina_received_request_bytes`        | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measures the size in bytes of the request received at the Executor level                                    |
| `jina_sent_response_bytes`        | [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) | Measures the size in bytes of the response returned from the Executor to the Gateway                           |



```{seealso} 
Beyond monitoring every endpoint of an Executor you can define {ref}`custom metrics <monitoring-executor>` for you 
Executor. 
```

```{hint} 
 `jina_receiving_request_seconds` is different from `jina_process_request_seconds` because it includes the gRPC communication overhead whereas `jina_process_request_seconds` is only about the time spend calling the function 
```

## See further

- {ref}`Defining custom metrics in an Executor <monitoring-executor>`
- {ref}`How to deploy and use the monitoring with Jina <monitoring>`
- [Using Grafana to visualize Prometheus metrics](https://grafana.com/docs/grafana/latest/getting-started/getting-started-prometheus/)
