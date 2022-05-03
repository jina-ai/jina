(monitoring)=
# How to deploy and use the monitoring with Jina

```{caution} 
The monitoring feature is still in Beta and the API is not stable yet.
```

Before starting showing you how to monitor a Flow, let me gave you some context on the monitoring stack.
To leverage the {ref}`metrics <monitoring-flow>` that Jina expose we recommend to use the Prometheus/Grafana stack. In this setup, Jina will expose different {ref}`metrics endpoint <monitoring-flow>`  , Prometheus will then be in charge of scrapping these endpoints and
to collect, aggregate and stored the different metrics. Prometheus will then allow external entity (like Grafana) to access these aggregated metrics via a query language [PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/).
Then the role of Grafana here will be to allow users to visualize these metrics by creating dashboard.

```{hint} 
Jina supports exposing the metrics, you are in charge of installing and managed your Prometheus/Grafana instance
```

We will show you in this guide how to easily deploy the Prometheus/Grafana stack and used them to monitor a Flow.

## Use Prometheus and Grafana to monitor a Flow on Kubernetes


One of the challenge of monitoring a Flow is to communicate to Prometheus the different metrics endpoints that the Flow expose.
Fortunately the [Prometheus operator for kubernetes](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md) makes all the process fairly easy because it can automatically discover new metrics endpoints to scrap.

```{hint} 
Deploying your Jina Flow on Kubernetes in the recommanded way to leverage the full potential of the monitoring feature because:
* The Prometheus operator can automatically discover new endpoint to scrap
* You can extend your monitoring with the rich built-in Kubernetes metrics
```

### Deploying Prometheus and Grafana

You need to have access to a kubernetes cluster to follow the rest of this guide.

```{hint} Local k8s Cluster
You can can easily have a kubernetes cluster on your local machine:
- [minikube](https://minikube.sigs.k8s.io/docs/)
- [microk8s](https://microk8s.io/)
``` 

```{hint} Cloud managed k8s cluster
You can use managed kubernetes solution:
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine),
- [Amazon EKS](https://aws.amazon.com/eks),
- [Azure Kubernetes Service](https://azure.microsoft.com/en-us/services/kubernetes-service),
```

#### 1 - Deploying Prometheus and Grafana

Deploying Prometheus and Grafana on your k8s cluster is as easy as executing the following line:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```
```{hint} 
setting the `serviceMonitorSelectorNilUsesHelmValues` to false allow the Prometheus Operator to discover metrics endpoint outside of the helm scope which will be needed to discover the Flow metrics endpoints.
```

#### 2 - Deploying the Flow

Let's now deploy the Flow that we want to monitor

```python
from jina import Flow

f = Flow(monitoring=True).add(uses='jinahub://SimpleIndexer')
f.to_k8s_yaml('config')
```


Then deploy the Flow

```bash
kubectl apply -R -f config
```

Wait for a couple of minutes, and you should see that the pods are ready:

```bash
kubectl get pods
```

```{figure} ../../../.github/2.0/kubectl_pods.png
:align: center
```

Then you can see that the new metrics endpoints are automatically discovered:
```bash
kubectl port-forward svc/prometheus-operated 9090:9090
```

```{figure} ../../../.github/2.0/prometheus_targets.png
:align: center
```

Now to acces Grafana just do

```bash
kb port-forward svc/prometheus-grafana 3000:80
```

and open `http://localhost:3000` in your browser


## Use Prometheus and Grafana to monitor a Flow with Docker compose

## Use Prometheus and Grafana to monitor a Flow locally

## See further

- {ref}`List of available metrics <monitoring-flow>`
- [Using Grafana to visualize prometheus metrics](https://grafana.com/docs/grafana/latest/getting-started/getting-started-prometheus/)
