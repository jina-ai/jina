(kubernetes)=
# Deploy with Kubernetes


```{tip}
This guide is designed for users who want to **manually** deploy a Jina project on Kubernetes.

Check out {ref}`jcloud` if you want a **one-click** solution to deploy and host Jina, leveraging a cloud-native stack of Kubernetes, Prometheus and Grafana, **without worrying about provisioning**.
```


:::::{grid} 2
:gutter: 3

::::{grid-item-card} {octicon}`cpu;1.5em` Deploy a Flow to JCloud
:link: fundamentals/jcloud/index
:link-type: doc
:class-card: color-gradient-card-2

JCloud is a free CPU/GPU hosting platform for Jina projects.
::::
:::::


Deploying a {class}`~jina.Flow` in Kubernetes is the recommended way to use Jina in production.

Since a {class}`~jina.Flow` is composed of {class}`~jina.Executor`s which can run in different runtimes depending on how you deploy
the Flow, Kubernetes can easily take over the lifetime management of Executors. 

In general, Jina follows the following principle when it comes to deploying in Kubernetes:
You, the user, know your use case and requirements the best.
This means that while Jina generates configurations for you that run out of the box, as a professional user you should
always see them as just a starting point to get you off the ground.

This how-to will go through deploying a simple Flow using Kubernetes, customizing the Kubernetes configuration
to your needs, and scaling Executors using replicas and shards.

## Preliminaries

To follow this how-to, you need access to a Kubernetes cluster.

You can either set up [`minikube`](https://minikube.sigs.k8s.io/docs/start/), or use one of many managed Kubernetes
solutions in the cloud:
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
- [Amazon EKS](https://aws.amazon.com/eks)
- [Azure Kubernetes Service](https://azure.microsoft.com/en-us/services/kubernetes-service)
- [Digital Ocean](https://www.digitalocean.com/products/kubernetes/)


(kubernetes-deploy)=
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

The example Flow here simply encodes and indexes text or image data using two Executors from [Executor Hub](https://hub.jina.ai/).
 
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

(kubernetes-replicas)=
## Scaling Executors: Replicas and shards

Jina supports two ways of scaling:

- **Replicas** can be used with any Executor type and are typically used for performance and availability.
- **Shards** are used for partitioning data and should only be used with indexers since they store state.

Check {ref}`here <scale-out>` for more information about these scaling mechanisms.

For shards, Jina creates a separate Deployment in Kubernetes per Shard.
Setting `f.add(..., shards=num_shards)` is sufficient to create a corresponding Kubernetes configuration.

For replicas, Jina uses [Kubernetes native replica scaling](https://kubernetes.io/docs/tutorials/kubernetes-basics/scale/scale-intro/) and **relies on a service mesh** to load balance requests between replicas of the same Executor.
Without a service mesh installed in your Kubernetes cluster, all traffic will be routed to the same replica.

````{admonition} See Also
:class: seealso

The impossibility of load balancing between different replicas is a limitation of Kubernetes in combination with gRPC.
If you want to learn more about this limitation, see [this](https://kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears/) Kubernetes Blog post.
````

### Install a service mesh

Service meshes work by attaching a tiny proxy to each of your Kubernetes pods, allowing for smart rerouting, load balancing,
request retrying, and host of other [features](https://linkerd.io/2.11/features/).

Jina relies on a service mesh to load balance request between replicas of the same Executor.
You can use your favourite Kubernetes service mesh in combination with your Jina Flow, but the configuration files
generated by `to_kubernetes_config()` already include all necessary annotations for the [Linkerd service mesh](https://linkerd.io).

````{admonition} Hint
:class: hint
You can use any service mesh with Jina, but Jina Kubernetes configurations come with Linkerd annotations out of the box.
````

To use Linkerd, [install the Linkerd CLI](https://linkerd.io/2.11/getting-started/).
After that, [install its control plane](https://linkerd.io/2.11/getting-started/) in your cluster.
This automatically sets up and manages the service mesh proxies when you deploy the Flow.

Once the Flow is deployed on Kubernetes, you can use all the native Kubernetes tools like `kubectl` to perform operations on the Pods and Deployments. 

You can use this to [add or remove replicas](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#scaling-a-deployment), to run [rolling update](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#updating-a-deployment) operations, etc ...

````{admonition} Caution
:class: caution

Many service meshes can perform retries themselves.
Be careful about setting up service mesh level retries in combination with Jina, as it may lead to unwanted behaviour in combination with
Jina's own {ref}`retry policy <flow-error-handling>`.

Instead, you can disable Jina level retries by setting `Flow(retries=0)` in Python, or `retries: 0` in the Flow
YAML `with` block.
````

````{admonition} Matching jina versions
:class: caution
If you change the Docker images in your Docker Compose generated file, ensure that all services included in the gateway are built with the same Jina version to guarantee compatibility.
````

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

## Scaling the Gateway
The Gateway is responsible for providing the API of the {ref}`Flow <flow>`.
If you have a large Flow with many Clients and many replicated Executors, the Gateway can become the bottleneck.
In this case you can also scale up the Gateway deployment to be backed by multiple Kubernetes Pods.
This is done by the regular means of Kubernetes: Either increase the number of replicas in the  {ref}`generated yaml configuration files <kubernetes-deploy>` or [add replicas while running](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#scaling-a-deployment).
To expose your Gateway replicas outside Kubernetes, you can add a load balancer as described {ref}`here <kubernetes-expose>`.

````{admonition} Hint
:class: hint
You can use a custom Docker image for the Gateway deployment by setting the envrironment variable `JINA_GATEWAY_IMAGE` to the desired image before generating the configuration.
````

## Extra Kubernetes options

You can't add basic Kubernetes feature like `Secrets`, `ConfigMap` or `Labels` via the Pythonic interface. This is intentional
and doesn't mean that we don't support these features. On the contrary, we let you fully express your Kubernetes configuration by using the Kubernetes API to add you own Kubernetes standard to Jina.

````{admonition} Hint
:class: hint
We recommend dumping the Kubernetes configuration files and then editing the files to suit your needs.
````

Here are possible configuration options you may need to add or change

- Add labels `selector`s to the Deployments to suit your case
- Add `requests` and `limits` for the resources of the different Pods 
- Set up persistent volume storage to save your data on disk
- Pass custom configuration to your Executor with `ConfigMap` 
- Manage credentials of your Executor with secrets
- Edit the default rolling update configuration


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

To put it briefly, there are just three key takeaways about deploying a Jina Flow on Kubernetes:

1. Use `f.to_kubernetes_yaml()` to generate Kubernetes configuration files from a Jina Flow object.
2. Modify the generated files freely - you know better what you need than we do!
3. Use a service mesh to enable replicated Executors.

## See also

- {ref}`Monitor the Flow once it is deployed <monitoring>`
- {ref}`See how failures and retries are handled <flow-error-handling>`
- {ref}`Learn more about scaling Executors <scale-out>`
