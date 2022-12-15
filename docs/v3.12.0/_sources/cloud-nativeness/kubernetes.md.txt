(kubernetes)=
# Deploy on Kubernetes

This how-to will go through deploying a simple Flow using Kubernetes, customizing the Kubernetes configuration
to your needs, and scaling Executors using replicas and shards.

Deploying a {class}`~jina.Flow` in Kubernetes is the recommended way to use Jina in production.

Since a {class}`~jina.Flow` is composed of {class}`~jina.Executor`s which can run in different runtimes depending on how you deploy
the Flow, Kubernetes can easily take over the lifetime management of Executors.  

```{seelaso}
This page is a step by step guide, refer to the {ref}`Kubernetes support documentation <kubernetes-docs>` for more details
```


```{hint}
This guide is designed for users who want to **manually** deploy a Jina project on Kubernetes.

Check out {ref}`jcloud` if you want a **one-click** solution to deploy and host Jina, leveraging a cloud-native stack of Kubernetes, Prometheus and Grafana, **without worrying about provisioning**.
```



## Preliminaries

To follow this how-to, you need access to a Kubernetes cluster.

You can either set up [`minikube`](https://minikube.sigs.k8s.io/docs/start/), or use one of many managed Kubernetes
solutions in the cloud:
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
- [Amazon EKS](https://aws.amazon.com/eks)
- [Azure Kubernetes Service](https://azure.microsoft.com/en-us/services/kubernetes-service)
- [Digital Ocean](https://www.digitalocean.com/products/kubernetes/)

You need to install Linkerd in your K8s cluster. To use Linkerd, [install the Linkerd CLI](https://linkerd.io/2.11/getting-started/) and [its control plane](https://linkerd.io/2.11/getting-started/) in your cluster.
This automatically sets up and manages the service mesh proxies when you deploy the Flow.

To understand why you need to install a service mesh like Linkerd refer to this  {ref}`section <service-mesh-k8s>`

## Deploy a simple Flow

By *simple* in this context we mean a Flow without replicated or sharded Executors - you can see how to use those in
Kubernetes {ref}`later on <kubernetes-replicas>`.

For now, define a Flow,
either in {ref}`YAML <flow-yaml-spec>` or directly in Python, as we do here:

```python
from jina import Flow

f = (
    Flow(port=8080)
    .add(name='encoder', uses='jinahub+docker://CLIPEncoder')
    .add(name='indexer', uses='jinahub+docker://AnnLiteIndexer', uses_with={'dim': 512})
)
```

You can essentially define any Flow of your liking.
Just ensure that all Executors are containerized, either by using *'jinahub+docker'*, or by {ref}`containerizing your local
Executors <dockerize-exec>`.

The example Flow here simply encodes and indexes text or image data using two Executors from [Executor Hub](https://cloud.jina.ai/).
 
Next, generate Kubernetes YAML configs from the Flow.
It's good practice to define a new Kubernetes namespace for that purpose:

```python
f.to_kubernetes_yaml('./k8s_flow', k8s_namespace='custom-namespace')
```

The following file structure will be generated - don't worry if it's slightly different -- there can be 
changes from one Jina version to another:

```
.
└── k8s_flow
    ├── gateway
    │   └── gateway.yml
    └── encoder
    │   └── encoder.yml
    └── indexer
        └── indexer.yml
```

You can inspect these files to see how Flow concepts are mapped to Kubernetes entities.
And as always, feel free to modify these files as you see fit for your use case.

````{admonition} Caution: Executor YAML configurations
:class: caution

As a general rule, the configuration files produced by `to_kubernets_yaml()` should run out of the box, and if you strictly
follow this how-to they will.

However, there is an exception to this: If you use a local dockerized Executor, and this Executors configuration is stored
in a file other than `config.yaml`, you will have to adapt this Executor's Kubernetes YAML.
To do this, open the file and replace `config.yaml` with the actual path to the Executor configuration.

This is because when a Flow contains a Docker image, it can't see what Executor
configuration was used to create that image.
Since all of our tutorials use `config.yaml` for that purpose, the Flow uses this as a best guess.
Please adapt this if you named your Executor configuration file differently.
````

Next you can actually apply these configuration files to your cluster, using `kubectl`.
This launches all Flow microservices.

First, create the namespace you defined earlier:

```shell
kubectl create namespace custom-namespace
```

Now, deploy this Flow to your cluster:
```shell
kubectl apply -R -f ./k8s_flow
```

Check that the Pods were created:
```shell
kubectl get pods -n custom-namespace
```

```text
NAME                              READY   STATUS    RESTARTS   AGE
encoder-8b5575cb9-bh2x8           1/1     Running   0          60m
gateway-7df8765bd9-xf5tf          1/1     Running   0          60m
indexer-8f676fc9d-4fh52           1/1     Running   0          60m
indexer-head-6fcc679d95-8mrm6     1/1     Running   0          60m
```

Note that the Jina gateway was deployed with name `gateway-7df8765bd9-xf5tf`.

Once you see that all the Deployments in the Flow are ready, you can start indexing documents:

```python
import portforward

from jina.clients import Client
from docarray import DocumentArray

with portforward.forward('custom-namespace', 'gateway-7df8765bd9-xf5tf', 8080, 8080):
    client = Client(host='localhost', port=8080)
    client.show_progress = True
    docs = client.post(
        '/index',
        inputs=DocumentArray.from_files('./imgs/*.png').apply(
            lambda d: d.convert_uri_to_datauri()
        ),
    )

    print(f' Indexed documents: {len(docs)}')
```

### Deploy Flow with shards and replicas

After your service mesh is installed, your cluster is ready to run a Flow with scaled Executors.
You can adapt the Flow from above to work with two replicas for the encoder, and two shards for the indexer:

```python
from jina import Flow

f = (
    Flow(port=8080)
    .add(name='encoder', uses='jinahub+docker://CLIPEncoder', replicas=2)
    .add(
        name='indexer',
        uses='jinahub+docker://ANNLiteIndexer',
        uses_with={'dim': 512},
        shards=2,
    )
)
```

Again, you can generate your Kubernetes configuration:

```python
f.to_kubernetes_yaml('./k8s_flow', k8s_namespace='custom-namespace')
```

Now you should see the following file structure:

```
.
└── k8s_flow
    ├── gateway
    │   └── gateway.yml
    └── encoder
    │   └─ encoder.yml
    └── indexer
        ├── indexer-0.yml
        ├── indexer-1.yml
        └── indexer-head.yml
```

Apply your configuration like usual:

````{admonition} Hint: Cluster cleanup
:class: hint
If you already have the simple Flow from the first example running on your cluster, make sure to delete it using `kubectl delete -R -f ./k8s_flow`.
````

```shell
kubectl apply -R -f ./k8s_flow
```


(kubernetes-expose)=
## Exposing the Flow
The previous examples use port-forwarding to index documents to the Flow. 
In real world applications, 
you may want to expose your service to make it reachable by users so that you can serve search requests.

```{caution}
Exposing the Flow only works if the environment of your `Kubernetes cluster` supports `External Loadbalancers`.
```

Once the Flow is deployed, you can expose a service:
```bash
kubectl expose deployment gateway --name=gateway-exposed --type LoadBalancer --port 80 --target-port 8080 -n custom-namespace
sleep 60 # wait until the external ip is configured
```

Export the external IP address. This is needed for the client when sending Documents to the Flow in the next section. 
```bash
export EXTERNAL_IP=`kubectl get service gateway-exposed -n custom-namespace -o=jsonpath='{.status.loadBalancer.ingress[0].ip}'`
```

### Client
The client:

- Sends an image to the exposed `Flow` on `$EXTERNAL_IP` 
- Retrieves the matches from the Flow.
- Prints the uris of the closest matches.

You should configure your Client to connect to the Flow via the external IP address as follows:

```python
import os
from jina.clients import Client

host = os.environ['EXTERNAL_IP']
port = 80

client = Client(host=host, port=port)

client.show_progress = True
docs = DocumentArray.from_files("./imgs/*.png").apply(
    lambda d: d.convert_uri_to_datauri()
)
queried_docs = client.post("/search", inputs=docs)

matches = queried_docs[0].matches
print(f"Matched documents: {len(matches)}")
```

## Update your Executor in Kubernetes

In Kubernetes, you can update your Executors by patching the Deployment corresponding to your Executor.

For instance, in the example above, you can change the CLIPEncoder's `batch_size` parameter by changing the content of the Deployment inside the `executor.yml` dumped by `.to_kubernetes_yaml`.

You need to add `--uses_with` and pass the batch size argument to it. This is passed to the container inside the Deployment:

```yaml
    spec:
      containers:
      - args:
        - executor
        - --name
        - encoder
        - --k8s-namespace
        - custom-namespace
        - --uses
        - config.yml
        - --port
        - '8080'
        - --uses-metas
        - '{}'
        - --uses-with
        - '{"batch_size": 64}'
        - --native
        command:
        - jina
```

After doing so, re-apply your configuration so the new Executor will be deployed without affecting the other unchanged Deployments:

```shell script
kubectl apply -R -f ./k8s_flow
```

````{admonition} Other patching options
:class: seealso

In Kubernetes Executors are ordinary Deployments, so you can use other patching options provided by Kubernetes:


- `kubectl replace` to replace an Executor using a complete configuration file
- `kubectl patch` to patch an Executor using only a partial configuration file
- `kubectl edit` to edit an Executor configuration on the fly in your editor

You can find more information about these commands in the [official Kubernetes documentation](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/).
````

## Key takeaways

In short, there are just three key steps to deploy a Jina Flow on Kubernetes:

1. Use `f.to_kubernetes_yaml()` to generate Kubernetes configuration files from a Jina Flow object.
2. Apply the generated file via `kubectl`(Modify the generated files if necessary)
3. Expose your Flow outside the K8s cluster

## See also
- {ref}`Kubernetes support documentation <kubernetes-docs>`
- {ref}`Monitor the Flow once it is deployed <monitoring>`
- {ref}`See how failures and retries are handled <flow-error-handling>`
- {ref}`Learn more about scaling Executors <scale-out>`
