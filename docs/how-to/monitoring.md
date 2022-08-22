(monitoring)=
# Monitor via Prometheus and Grafana

First, let's have some context on the monitoring stack that we will be using during this guide.
To leverage the {ref}`metrics <monitoring-flow>` that Jina exposes, we recommend using the Prometheus/Grafana stack. In this setup, Jina will expose different {ref}`metrics endpoint <monitoring-flow>`, and Prometheus will then be in charge of scraping these endpoints, as well as
collecting, aggregating, and storing the different metrics. Prometheus will then allow external entities (like Grafana) to access these aggregated metrics via the query language [PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/).
Then the role of Grafana here will be to allow users to visualize these metrics by creating dashboards.

```{hint} 
Jina supports exposing the metrics, you are in charge of installing and managing your Prometheus/Grafana instances.
```

We will show you in this guide how to easily deploy the Prometheus/Grafana stack and used them to monitor a Flow.

(deploy-flow-monitoring)=
## Deploying the Flow and the monitoring stack

### Deploying on Kubernetes


One of the challenges of monitoring a {class}`~jina.Flow` is communicating its different metrics endpoints to Prometheus.
Fortunately, the [Prometheus operator for Kubernetes](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md) makes the process fairly easy, because it can automatically discover new metrics endpoints to scrape.

Deploying your Jina Flow on Kubernetes is the recommended way to leverage the full potential of the monitoring feature because:
* The Prometheus operator can automatically discover new endpoints to scrape
* You can extend your monitoring with the rich built-in Kubernetes metrics

Deploying Prometheus and Grafana on your k8s cluster is as easy as executing the following line:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```
```{hint} 
setting the `serviceMonitorSelectorNilUsesHelmValues` to false allows the Prometheus Operator to discover metrics endpoint outside of the helm scope which will be needed to discover the Flow metrics endpoints.
```

Let's now deploy the Flow that we want to monitor:



````{tab} via YAML
This example shows how to start a Flow with monitoring enabled via yaml:

In a `flow.yaml` file
```yaml
jtype: Flow
with:
  monitoring: true
executors:
- uses: jinahub://SimpleIndexer
```

```bash
jina export kubernetes flow.yml ./config ```
````

````{tab} via Python API
```python
from jina import Flow

f = Flow(monitoring=True).add(uses='jinahub+docker://SimpleIndexer')
f.to_kubernetes_yaml('config')
```
````

This will create a `config` folder containing the Kubernetes YAML definition of the Flow.

```{seealso}
You can see in-depth how to deploy a Flow on kubernetes {ref}`here <kubernetes>`
```

Then deploy the Flow:

```bash
kubectl apply -R -f config
```

Wait for a couple of minutes, and you should see that the Pods are ready:

```bash
kubectl get pods
```

```{figure} ../../.github/2.0/kubectl_pods.png
:align: center
```

Then you can see that the new metrics endpoints are automatically discovered:

```bash
kubectl port-forward svc/prometheus-operated 9090:9090
```

```{figure} ../../.github/2.0/prometheus_target.png
:align: center
```
Before querying the gateway you need to port-forward
```bash
kubectl port-forward svc/gateway 8080:8080
```



Now to access Grafana just do

```bash
kb port-forward svc/prometheus-grafana 3000:80
```

and open `http://localhost:3000` in your browser

User is `admin`, password is `prom-operator`

You should see the Grafana home page.


### Deploying locally

Let's first deploy the Flow that we want to monitor:


````{tab} via Python code
```python
from jina import Flow

with Flow(monitoring=True, port_monitoring=8000, port=8080).add(
    uses='jinahub://SimpleIndexer', port_monitoring=9000
) as f:
    f.block()
```
````

````{tab} via docker-compose
```python
from jina import Flow

Flow(monitoring=True, port_monitoring=8000, port=8080).add(
    uses='jinahub+docker://SimpleIndexer', port_monitoring=9000
).to_docker_compose_yaml('config.yaml')
```
```bash
docker-compose -f config.yaml up
```
````

To monitor a flow locally you will need to install Prometheus and Grafana locally. The easiest way to do it is by using
Docker Compose

First clone the repo which contains the config file:

```bash
git clone https://github.com/jina-ai/example-grafana-prometheus
cd example-grafana-prometheus/prometheus-grafana-local
```

then 

```bash
docker-compose up
```

You can access the Grafana dashboard at `http://localhost:3000`. the username is `admin` and the password `foobar`.

```{caution}
This example is working locally because Prometheus is configured so that it listens to ports 8000 and 9000. However,
in contrast with deploying on Kubernetes, you need to tell Prometheus which port to look at. You can change these
ports by modifying this [file](https://github.com/jina-ai/example-grafana-prometheus/blob/8baf519f7258da68cfe224775fc90537a749c305/prometheus-grafana-local/prometheus/prometheus.yml#L64)
```

### Deploying on Jcloud
In case your Flow is deployed on JCloud, there is no need to provision a monitoring stack yourself. Prometheus and Grafana are 
handled by JCloud and you can find a dashboard URL using the command `jc status <flow_id>`

## Using Grafana to visualize metrics

Once you can access the Grafana homepage then go to `Browse` then `import` and copy and paste the [JSON file](https://github.com/jina-ai/example-grafana-prometheus/blob/main/grafana-dashboards/flow.json) 


You should see the following dashboard:

```{figure} ../../.github/2.0/grafana.png
:align: center
```


````{admonition} Hint
:class: hint

You should query your Flow generate the first metrics. Othewise the dashboard will look empty.
````

You can query the flow by doing :

```python
from jina import Client, DocumentArray

client = Client(port=51000)
client.index(inputs=DocumentArray.empty(size=4))
client.search(inputs=DocumentArray.empty(size=4))
```

## See further

- {ref}`List of available metrics <monitoring-flow>`
- [Using Grafana to visualize Prometheus metrics](https://grafana.com/docs/grafana/latest/getting-started/getting-started-prometheus/)
- {ref}`Defining custom metrics in an Executor <monitoring-executor>`
