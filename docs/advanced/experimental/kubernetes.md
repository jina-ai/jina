(kubernetes)=
# Jina on Kubernetes

Jina natively supports deploying your Flow and Executors into Kubernetes.

## Preliminaries

Please first set up a `Kubernetes` cluster and configure the cluster access locally.

```{tip}
For local testing [`minikube`](https://minikube.sigs.k8s.io/docs/start/) is recommended.
```

```{seealso}

Here are some managed `Kubernetes` cluster solutions you could use:

- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine),
- [Amazon EKS](https://aws.amazon.com/eks),
- [Azure Kubernetes Service](https://azure.microsoft.com/en-us/services/kubernetes-service),
- [Digital Ocean](https://www.digitalocean.com/products/kubernetes/)
```

## Deploy your `Flow`

To deploy a `Flow` on `Kubernetes`, first, you have to generate kubernetes YAML configuration files from a Jina Flow.
Then, you can use the `kubectl apply` command to create or update your Flow resources within your cluster.

```{caution}
All Executors in the Flow should be used with `jinahub+docker://...` or `docker://...`.
```

To generate YAML configurations for Kubernetes from a Jina Flow, one just needs to call:

```python
flow.to_k8s_yaml('flow_k8s_configuration')
```

This will create a folder 'flow_k8s_configuration' with a set of Kubernetes yaml configurations for all the deployments composing the Flow

## Examples

### Indexing and searching images using CLIP image encoder and PQLiteIndexer

This example shows how to build and deploy a Flow in Kubernetes with [`CLIPImageEncoder`](https://hub.jina.ai/executor/0hnlmu3q) as encoder and [`PQLiteIndexer`](https://hub.jina.ai/executor/pn1qofsj) as indexer.

```python
from jina import Flow

f = Flow(port_expose=8080, protocol='http').add(
    name='encoder', uses='jinahub+docker://CLIPImageEncoder', replicas=2
).add(name='indexer', uses='jinahub+docker://PQLiteIndexer', uses_with={'dim': 512}, shards=2)
```

Now, we can generate Kubernetes YAML configs from the Flow:

```python
f.to_k8s_yaml('./k8s_flow', k8s_namespace='custom-namespace')
```

You should expect the following file structure generated:

```
.
└── k8s_flow
    ├── gateway
    │   └── gateway.yml
    └── encoder
    │   ├── encoder.yml
    │   └── encoder-head-0.yml
    └── indexer
        ├── indexer-0.yml
        ├── indexer-1.yml
        └── indexer-head-0.yml
```

As you can see, the Flow contains configuration for the gateway and the rest of executors

Now, you can deploy this Flow to you cluster in the following way:
```shell
kubectl apply -f ./k8s_flow
```

Once we see that all the Deployments in the Flow are ready, we can start indexing documents.

```python
import os
import portforward

from jina.clients import Client
from jina import DocumentArray

config_path = os.environ['KUBECONFIG']

with portforward.forward(
    'custom-namespace', 'gateway', 8080, 8080, config_path
):
    client = Client(host='localhost', port=8080)
    client.show_progress = True
    indexed_documents = []
    for resp in client.post(
        '/index', inputs=DocumentArray.from_files('./imgs/*.jpg'), return_results=True
    ):
        indexed_documents.extend(resp.docs)

    print(f' Indexed documents: {[doc.uri for doc in indexed_documents]}')
```

```{admonition} Caution
:class: caution
We heavily recommend you to deploy each `Flow` into a separate namespace. In particular it should not be deployed into namespaces, where other essential non Jina services are running. 
If `custom-namespace` has been used by another `Flow`, please set a different `k8s_namespace` name.
```

```{admonition} Caution
:class: caution
In the default deployment dumped by the Flow, no Persistent Volume Object is added. You may want to edit the deployment files to add them if needed.
```

## Exposing your `Flow`
The previous examples use port-forwarding to index documents to the `Flow`. 
Thinking about real world applications, 
you might want to expose your service to make it reachable by the users, so that you can serve search requests

```{caution}
Exposing your `Flow` only works if the environment of your `Kubernetes cluster` supports `External Loadbalancers`.
```

Once the `Flow` is deployed, you can expose a service.
```bash
kubectl expose deployment gateway --name=gateway-exposed --type LoadBalancer --port 80 --target-port 8080 -n custom-namespace
sleep 60 # wait until the external ip is configured
```

Export the external ip which is needed for the client in the next section when sending documents to the `Flow`. 
```bash
export EXTERNAL_IP=`kubectl get service gateway-exposed -n custom-namespace -o=jsonpath='{.status.loadBalancer.ingress[0].ip}'`
```

### Client
The client sends an image to the exposed `Flow` on `$EXTERNAL_IP` and retrieves the matches retrieved from the Flow.
Finally, it prints the uri of the closest matches.

```python
import requests
from jina import DocumentArray
import os
host = os.environ['EXTERNAL_IP']
port = 80
url = f'http://{host}:{port}'
doc = DocumentArray.from_files('./imgs/*.jpg')[0].dict()
resp = requests.post(f'{url}/search', json={'data': [doc]})
closest_match_uri = resp.json()['data']['docs'][0]['matches'][0]['uri']
print('closest_match_uri: ', closest_match_uri)
```

## Scaling Executors on Kubernetes

In Jina we support two ways of scaling:
- **Replicas** can be used with any Executor type and is typically used for performance and availability.
- **Shards** are used for partitioning data and should only be used with Indexers since they store a state.

Check {ref}`here <flow-topology>` for more information.

Jina creates a separate Deployment in Kubernetes per Shard and uses [Kubernetes native replica scaling](https://kubernetes.io/docs/tutorials/kubernetes-basics/scale/scale-intro/) to create multiple Replicas per Shard.

