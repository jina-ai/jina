# Jina on Kubernetes

Jina natively supports Kubernetes and you can use it via Flow API.

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

To deploy a `Flow` on `Kubernetes`, you have to set `infrastructure='K8S'` when creating the `Flow`.

```{caution}
All Executors in the Flow should be used with `jinahub+docker://`.
```

## Examples

### CLIP image encoder

#### Server

The following code deploys a simple `Flow` with just a single `Executor`.

```python
from jina import Flow

f = Flow(name='index-flow', port_expose=8080, infrastructure='K8S', protocol='http').add(
    uses='jinahub+docker://CLIPImageEncoder'
)

with f:
    f.block()
```

After the deployment finished, set up port forwarding to enable the client to send requests to the `Flow`.

```bash
kubectl port-forward svc/gateway -n index-flow 8080:8080 &
```

#### Client

Once the port forward is set up, you can request embeddings for images.

```python
import base64

import numpy as np
import requests
from jina import Document

# since port forwarding is running, you can run requests to localhost on 8080
host = '127.0.0.1'
port = 8080

url = f'http://{host}:{port}'

doc = Document(id=f'image', blob=np.random.rand(3, 16, 16)).dict()

resp = requests.post(f'{url}/index', json={'data': [doc]})
embedding = np.frombuffer(
    base64.decodebytes(
        resp.json()['data']['docs'][0]['embedding']['dense']['buffer'].encode()
    ),
    np.float32,
)

print(embedding)
```

### Postgres indexer

This example deploys the index `Flow` on `Kubernetes`

```{caution}
In this example, we assume that there is a postgres database deployed on `Kubernetes` already. 
You can also modify the database configuration to use a postgres database outside the `Kubernetes` cluster.
```

#### Index server

```python
from jina import Flow

f = Flow(
    name='index-flow', port_expose=8080, infrastructure='K8S', protocol='http'
).add(
    # name of the service and deployment in Kubernetes
    name='test_searcher',
    # executor has to be containerized
    uses='jinahub+docker://FaissPostgresSearcher',
    # database configuration
    uses_with={
        'hostname': f'postgres.postgres.svc.cluster.local',
        'username': 'postgresadmin',
        'database': 'postgresdb',
        'table': 'test_searcher',
    },
)

with f:
    f.block()
```

Use `port-forward` to send requests to the gateway of the index `Flow`:

```bash
kubectl port-forward svc/gateway -n index-flow 8080:8080 &
```

#### Index client

On the client side, let's index 100 `Documents`:

```python
import numpy as np
import requests
from jina import Document

ip = '127.0.0.1'
port = 8080
host = f'http://{ip}:{port}'

docs = [
    Document(id=f'item {i}', embedding=np.random.rand(128).astype(np.float32)).dict()
    for i in range(100)
]
for d in docs:
    print('index document:', d['id'])
    resp = requests.post(f'{host}/index', json={'data': [d]})
    print(resp.text)
```

#### Search server

The following code deploys a search `Flow` on `Kubernetes`. In total, there are 9 `Kubernetes` deployments and services
created.

- one gateway
- 2 x 3 shards, since the deployed `Executor` has 3 shards which have 2 replicas each
- a head which is used to fan-out the request to the shards
- a tail to fan-in and merge the search results from all shards

Visualization of the deployments:

```
                 shard0_replica0, shard0_replica1
               /                                  \
gateway - head - shard1_replica0, shard1_replica1 - tail 
               \                                  /
                 shard2_replica0, shard2_replica1
```

Deploy search `Flow`:

```python
from jina import Flow

shards = 3

f = Flow(
    name='search-flow', port_expose=8080, infrastructure='K8S', protocol='http'
).add(
    # name of the service and deployment in Kubernetes
    name='test_searcher',
    shards=shards,
    replicas=2,
    uses='jinahub+docker://FaissPostgresSearcher',
    uses_with={
        'startup_sync_args': {'only_delta': True},
        'total_shards': shards,
        'hostname': f'postgres.postgres.svc.cluster.local',
        'username': 'postgresadmin',
        'database': 'postgresdb',
        'table': 'test_searcher',
    },
    uses_after='jinahub+docker://MatchMerger',
)

with f:
    f.block()
```

Use `port-forward` to send requests to the gateway of the search `Flow`:

```bash
kubectl port-forward svc/gateway -n search-flow 8081:8080 &
```

#### Search client

Get search results for a single `Document`:

```python
import numpy as np
import requests
from jina import Document

ip = '127.0.0.1'
port = '8081'
host = f'http://{ip}:{port}'

data = [Document(embedding=np.random.rand(128).astype(np.float32)).dict()]

resp = requests.post(f'{host}/search', json={'data': data})
print(f"Len response matches: {len(resp.json()['data']['docs'][0]['matches'])}")
```

```{admonition} Limitations of the Current Implemenation
:class: caution

- each `Executor` has to be containerized
- only stateless executors are supported when using replicas > 1
- `Kubernetes` is doing `L4` (Network Layer) loadbalancing. 
  Means, each new connection is loadbalanced to one of the replicas.
  However, `Executors` are using long-living TCP connections set up by `gRPC` 
  and send multiple requests over the same connection. 
  Since `Kubernetes` can only loadbalance requests when new connections are established, 
  all requests are sent to the same replica.
  This problem can be fixed by injecting a proxy into all `Kubernetes` pods.
  We recommend using `envoy`. It captures all in-going and out-going network traffic and
  maintains long-living TCP connections to all replicas. 
  It loadbalances out-going requests to make sure the workload is evenly distributed among all replicas.
  Therefore, it allows loadbalancing on `L7` (Application Layer).
  Please inject the `envoy` proxy yourself for now.
  You can use the service mesh `Istio` to automatically inject `envoy` proxies into the `Executor` `Pods` as sidecar.
```