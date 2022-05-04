(monitoring-flow)=
# Monitor Flow

```{caution} 
The monitoring feature is still in Beta and the API is not stable yet.
```

A Jina {ref}`Flow <flow-cookbook>` exposes several core metrics that allow you to have a deeper look
on what is happening inside it. Metrics are particularly useful for building dashboards and alerts, with them, you can, for example, monitor the overall performance 
of your Flow, detect bottleneck, alert your team when some component of your Flow are down.

Jina Flow expose metrics in the [prometheus format](https://prometheus.io/docs/instrumenting/exposition_formats/) which
is plain text that is both understandable by human and machine. These metrics are intended to be scrap by [prometheus](https://prometheus.io/). 
We encourage you to visualize metrics with [grafana](https://grafana.com/)


## Using the monitoring in a Flow

A {ref}`Flow <flow-cookbook>` is composed of several Pods namely the Gateway and the Executors (potentially a Head as well). 
see the {ref}`architecture overview <architecture-overview>` for more details. Each of these Pods are microservices which communicate 
by gRPC. They will expose their own metrics using the [prometheus client](https://prometheus.io/docs/instrumenting/clientlibs/).
It means that they are as many metrics endpoints that they are Pods in your Flow. 

Lets gave an example to illustrate it :

````{tab} via Python API

This example shows how to start a Flow with monitoring enable via the Python API:

```python
from jina import Flow

with Flow(monitoring=True, port_monitoring=9090).add(
    uses='jinahub://SimpleIndexer', port_monitoring=9091
) as f:
    f.block()
```
````

````{tab} via YAML
This example shows how to start a Flow with monitoring enable via yaml:

In a `flow.yaml` file
```yaml
!Flow
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

This Flow will create two Pods, one for the Gateway, one for the SimpleIndexer Executor, and therefore it will create two 
metrics endpoint:

* `http://localhost:9090  ` for the gateway
* `http://localhost:9091  ` for the SimpleIndexer

````{admonition} Default Monitoring port
:class: hint
The default monitoring port is `9090`, if you want to enable the monitoring on both the Gateway and the Executors you need to specifiy
the `prometheus_port` for the Executors. 
````


Because each Pods in a Flow expose its own metrics the monitoring feature could be used independently on each Pod.
It means that you are not forced to always monitor each Pods of your Flow. For example, you could be only interested in
metrics coming from the Gateway, and therefore you only activate the monitoring on it. On the other hand you might be only
interested in monitoring a single Executor. Note that by default the monitoring is disabled everywhere.

To enable the monitoring you need to pass `monitoring = True` when creating the Flow.
```python
Flow(monitoring=True).add(...)
```
This will enable the monitoring on *all the Pods* of your Flow. 

If you want to enable the monitoring only on the Gateway you should once you enabled it on the Flow level, disable it for 
all the other Executor.

```python
Flow(monitoring=True).add(monitoring=False, ...).add(monitoring=False, ...)
```

On the other hand, If you want to only enable the monitoring on a given Executor you should do:
```python
Flow().add(...).add(uses=MyExecutor, monitoring=True)
```

## Available metrics

We support different metrics in the Flow, and we will later allow users to define their own.

Because all the Pods don't have the same role, they expose different kind of metrics:


### Gateway Pods

| Metrics name                       | Metrics type | Description                                                                                                                                                                                                                                                                |
|------------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds`   |   Summary    | Measure the time elapsed between receiving a request from the client and the sending back the response.                                                                                                                                                                    |
| `jina_sending_request_seconds`     |   Summary    | Measure the time elapsed between sending a downstream request to an Executor/Head and receiving the response back.                                                                                                                                                         |

### Head Pods

| Metrics name                       | Metrics type | Description                                                                                                     |
|------------------------------------|--------------|-----------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds`   |   Summary    | Measure the time elapsed between receiving a request from the gateway and the sending back the response.        |
| `jina_sending_request_seconds`     |   Summary    | Measure the time elapsed between sending a downstream request to an Executor and receiving the response back.   |

### Executor Pods

| Metrics name                     | Metrics type | Description                                                                                                           |
|----------------------------------|--------------|-----------------------------------------------------------------------------------------------------------------------|
| `jina_receiving_request_seconds` | Summary      | Measure the time elapsed between receiving a request from the gateway(or the head) and the sending back the response. |
| `jina_process_request_seconds`   | Summary      | Measure the time spend calling the requested method                                                                   |
| `jina_document_processed_total`  | Counter      | Count the number of Document processed by an Executor                                                                 |

```{hint} 
 `jina_receiving_request_seconds` is different from `jina_process_request_seconds` because it includes the gRPC communication overhead whereas `jina_process_request_seconds` is only about the time spend calling the function 
```


## See further

- {ref}`How to deploy and use the monitoring with Jina <monitoring>`
- [Using Grafana to visualize prometheus metrics](https://grafana.com/docs/grafana/latest/getting-started/getting-started-prometheus/)
