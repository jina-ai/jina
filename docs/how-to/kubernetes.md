(kubernetes)=
# Deploy with Kubernetes


```{tip}
This guide is designed for users who want to **manually** deploy Jina project on Kubernetes.

If you are looking for a **one-click** solution to deploy and host Jina, meanwhile leveraging cloud-native stack such as Kubernetes, Prometheus and Grafana, **without worrying about provisioning**, please check out {ref}`jcloud`.
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


Deploying a {class}`~jina.Flow` in Kubernetes is the recommended way of using Jina in production.

Since a {class}`~jina.Flow` is composed of {class}`~jina.Executor`s which can run in different runtimes depending on how you want to deploy
your Flow, Kubernetes can easily take over the lifetime management of Executors. 

In general, Jina follows the following principle when it comes to deploying in Kubernetes:
You, the user, know your use case and requirements the best.
This means that while Jina generates configurations for you that run out of the box, as a professional user you should
always see them as just a starting point to get you off the ground.

In this how-to you will go through how to deploy a simple Flow using Kubernetes, how to customize the Kubernetes configuration
to your needs, and how to scale Executors using replicas and shards.



## Preliminaries

To follow along with this how-to, you will need access to a Kubernetes cluster.

You can either set up [`minikube`](https://minikube.sigs.k8s.io/docs/start/), or use one of many managed Kubernetes
solutions in the cloud:
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
- [Amazon EKS](https://aws.amazon.com/eks)
- [Azure Kubernetes Service](https://azure.microsoft.com/en-us/services/kubernetes-service)
- [Digital Ocean](https://www.digitalocean.com/products/kubernetes/)


(kubernetes-deploy)=
## Deploy a simple Flow

By *simple* in this context we mean a Flow without replicated or sharded Executors - you will see how to use those in
Kubernetes {ref}`later on <kubernetes-replicas>`.

For now, define a Flow.
You can either do this through the Flow {ref}`YAML interface <flow-yaml-spec>` or directly in Python, like we do here:

```python
from jina import Flow

f = (
    Flow(port=8080)
    .add(name='encoder', uses='jinahub+docker://CLIPEncoder')
    .add(name='indexer', uses='jinahub+docker://AnnLiteIndexer', uses_with={'dim': 512})
)
```

Here you can essentially define any Flow of your liking.
Just make sure that all Executors are containerized, either by using *'jinahub+docker'*, or by {ref}`containerizing your local
Executors <dockerize-exec>`.

The example Flow here simply encodes and indexes text or image data using two Executors from the [Jina Hub](https://hub.jina.ai/).
 
Next, you can generate Kubernetes YAML configs from the Flow.
It is good practice to define a new Kubernetes namespace for that purpose:

```python
f.to_kubernetes_yaml('./k8s_flow', k8s_namespace='custom-namespace')
```

You should expect the following file structure to be generated - don't worry if it is slightly different, there can be 
changes to this from one Jina version to the other:

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
And as always, feel free to modify these config files as you see fit for your use case.

````{admonition} Caution: Executor YAML configurations
:class: caution

As a general rule, the configuration files produced by `to_kubernets_yaml()` should run out of the box, and if you strictly
follow this how-to they will.

However, there is an exception to this: If you use a local dockerized Executor, and this Executors configuration is stored
in a file other than `config.yaml`, you will have to adapt this Executor's Kubernetes YAML.
To do this, open the file and replace `config.yaml` with the actual path to the Executor configuration.

The reason for this is that when a Flow is defined by being passed a Docker image, it has no knowledge of what Executor
configuration was used to create that image.
Since all of our Tutorials use `config.yaml` for this purpose, the Flow can only use this as a best guess.
Please adapt this if you used a differently named Executor configuration file.
````

Next you can actually apply these configuration files to your cluster, using `kubectl`.
This will launch all Flow microservices.

First, create the namespace you defined earlier:

```shell
kubectl create namespace custom-namespace
```

Now, you can deploy this Flow to you cluster in the following way:
```shell
kubectl apply -R -f ./k8s_flow
```

We can check that the pods were created:
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

Once you see that all the Deployments in the Flow are ready, you can start indexing documents.

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
## Scaling Executors: Flow with replicas and shards

Jina supports two ways of scaling:

- **Replicas** can be used with any Executor type and is typically used for performance and availability.
- **Shards** are used for partitioning data and should only be used with indexers since they store state.

Check {ref}`here <scale-out>` for more information about these scaling mechanisms.

For shards, Jina creates a separate Deployment in Kubernetes per Shard.
Setting `f.add(..., shards=num_shards)` is sufficient to create a corresponding Kubernetes configuration.

For replicas, Jina uses [Kubernetes native replica scaling](https://kubernetes.io/docs/tutorials/kubernetes-basics/scale/scale-intro/) and **relies on a service mesh** to load balance request between replicas of the same Executor.
Without a service mesh installed in your Kubernetes cluster, all the traffic will be routed to the same replica.

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

To install Linkerd, you first have to [install the Linkerd CLI](https://linkerd.io/2.11/getting-started/).
After that, you [install its control plane](https://linkerd.io/2.11/getting-started/) in your cluster.
This is what will automatically set up and manage the service mesh proxies when you deploy your Flow.


Once the Flow is deployed on Kubernetes, you can use all the native Kubernetes tools like `kubectl` to perform operations on the Pods and Deployments. 

You can use this to [add or remove replicas](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#scaling-a-deployment), to run [rolling update](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#updating-a-deployment) operations, etc ...

````{admonition} Caution
:class: caution

Many service meshes have the ability to perform retries themselves.
Be careful about setting up service mesh level retries in combination with Jina, as it may lead to unwanted behaviour in combination with
Jina's own {ref}`retry policy <flow-error-handling>`.

Instead, you may want to disable Jina level retries by setting `Flow(retries=0)` in Python, or `retries: 0` in the Flow
YAML `with` block.
````

````{admonition} Matching jina versions
:class: caution
If you change the Docker images in your Docker Compose generated file, ensure that all the services included in the gateway are built with the same Jina version to guarantee compatibility.
````

### Deploy your Flow with shards and replicas

After your service mesh is installed, your cluster is ready to run a Flow with scaled Executors.
You can adapt your Flow from above to work with two replicas for the encoder, and two shards for the indexer:

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

Again, you can generate your Kubernetes configurations:

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

And you can apply your configuration like usual:

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
You can use a custom Docker image for the Gateway deployment. Just set the envrironment variable `JINA_GATEWAY_IMAGE` to the desired image before generating the configuration.
````

## Extra Kubernetes options

One could see that you can't add basic Kubernetes feature like `Secrets`, `ConfigMap` or `Lables` via the pythonic interface. That is intended
and it does not mean that we don't support these features. On the contrary we allow you to fully express your Kubernetes configuration by using the Kubernetes API so that you can add you own Kubernetes standard to jina.

````{admonition} Hint
:class: hint
We recommend dumping the Kubernetes configuration files and then editing the files to suit your needs.
````

Here are possible configuration options you may need to add or change

- Add labels `selector`s to the Deployments to suit your case
- Add `requests` and `limits` for the resources of the different Pods 
- Setup persistent volume storage to save your data on disk
- Pass custom configuration to your Executor with `ConfigMap` 
- Manage the credentials of your Executor with secrets
- Edit the default rolling update configuration


(kubernetes-expose)=
## Exposing your Flow
The previous examples use port-forwarding to index documents to the Flow. 
Thinking about real world applications, 
you might want to expose your service to make it reachable by the users, so that you can serve search requests

```{caution}
Exposing your Flow only works if the environment of your `Kubernetes cluster` supports `External Loadbalancers`.
```

Once the Flow is deployed, you can expose a service.
```bash
kubectl expose deployment gateway --name=gateway-exposed --type LoadBalancer --port 80 --target-port 8080 -n custom-namespace
sleep 60 # wait until the external ip is configured
```

Export the external ip which is needed for the client in the next section when sending documents to the Flow. 
```bash
export EXTERNAL_IP=`kubectl get service gateway-exposed -n custom-namespace -o=jsonpath='{.status.loadBalancer.ingress[0].ip}'`
```

### Client
The client sends an image to the exposed `Flow` on `$EXTERNAL_IP` and retrieves the matches retrieved from the Flow.
Finally, it prints the uri of the closest matches.

You will need to configure your Client to connect to the Flow via the external IP by doing:

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


For instance, in the example above, you may want to change set a `batch_size` parameter for the CLIPEncoder.

To do this, change the content of the Deployment inside the `executor.yml` dumped by `.to_kubernetes_yaml`.

You need to add `--uses_with` and pass the batch size argument to it. This will be passed to the container inside the Deployment:

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

After doing so, you can re-apply your configuration and the new Executor will be deployed without affecting the other unchanged Deployments:

```shell script
kubectl apply -R -f ./k8s_flow
```

````{admonition} Other patching options
:class: seealso

Within Kubernetes, Executors are ordinary Deployments.
This means that you can use other patching options provided by Kubernetes:


- `kubectl replace` to replace an Executor using a complete configuration file
- `kubectl patch` to patch an Executor using only a partial configuration file
- `kubectl edit` to edit an Executor configuration on the fly in your editor

You can find more information about these commands in the [official Kubernetes documentation](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/).
````

## Key takeaways

To put it succinctly, there are just three key takeaways about deploying a Jina Flow using Kubernetes:

1. Use `f.to_kubernetes_yaml()` to generate Kubernetes configuration files from a Jina Flow object
2. Modify the generated files freely - you know better what you need than we do!
3. To enable replicated Executors, use a service mesh

## See also

- {ref}`Monitor your Flow once it is deployed <monitoring>`
- {ref}`See how failures and retries are handled <flow-error-handling>`
- {ref}`Learn more about scaling Executors <scale-out>`
