# Jina On Kubernetes

Deploy your `Flow` on `Kubernetes`.
## Requirements
Please setup a `Kubernetes` cluster and pull the credentials.

For local testing `minikube` is recommended.
- [minikube](https://minikube.sigs.k8s.io/docs/start/), 
  
Here are some managed `Kubernetes` cluster solutions you could use:
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine),
- [Amazon EKS](https://aws.amazon.com/eks),
- [Azure Kubernetes Service](https://azure.microsoft.com/en-us/services/kubernetes-service),
- [Digital Ocean](https://www.digitalocean.com/products/kubernetes/)
  
## Deploy Your `Flow`
To deploy a `Flow` on `Kubernetes`, you have to set the `infrastructure='K8S'` when creating the `Flow`.
```{caution}
All Executors in the Flow should be used with `jinahub+docker://`.
```

## Example 1 - CLIP Image Encoder
The following code deploys a simple `Flow` with just one `Executor`.
```python
from jina import Flow

flow = Flow(
    name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
).add(
    uses='jinahub+docker://CLIPImageEncoder',
)
flow.start()

```
After the deployment finished, run a port forward to run client requests.
```bash
kubectl port-forward svc/gateway -n index-flow 8080:8080 &
```

Once the port forward setup, you can request embeddings for images.
```python
import base64

import numpy as np
import requests
from jina import Document

host = '127.0.0.1'
port = 8080

url = f'http://{host}:{port}'

doc = Document(id=f'image',blob=np.random.rand(3, 16, 16)).dict()

resp = requests.post(f'{url}/index', json={'data': [doc]})
embedding = np.frombuffer(
    base64.decodebytes(
        resp.json()['data']['docs'][0]['embedding']['dense']['buffer'].encode()
    ), np.float32)
print(embedding)

```


## Example 2 - Postgres Indexer
In this example, we assume that, there is a postgres database deployed on `Kubernetes` already. 
You can also modify the database configuration to use a postgres database outside the `Kubernetes` cluster.
Deploy the index `Flow` on `Kubernetes`:
```python
from jina import Flow

flow = Flow(
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
    }
)
flow.start()
```
Use `port-forward` to send requests to the gateway of the index `Flow`.
```bash
kubectl port-forward svc/gateway -n index-flow 8080:8080 &
```

Index 100 `Documents`.
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

The following code deploys a search `Flow` on `Kubernetes`.
In total, there are 9 `Kubernetes` deployments and services created 
- one gateway
- 3 x 2 shards, since the deployed `Executor` has 3 shards which have 2 replicas each
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

flow = Flow(
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
flow.start()
```
Use `port-forward` to send requests to the gateway of the search `Flow`.
```bash
kubectl port-forward svc/gateway -n search-flow 8081:8080 &
```

Find `top-k` results for a single `Document`:
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

## Limitations
- each `Executor` has to be containerized
- only stateless executors are supported when using replicas > 1
- `Kubernetes` is doing `L4` (Network Layer) loadbalancing.
  Since the `Executors` are using long-living `gRPC` connections,
  loadbalancing has to be done on `L7` level (Application Layer).
  We recommend using proxy based loadbalancing via `envoy`.
  Please inject the `envoy` proxy yourself for now.
  You can use the service mesh `Istio` to automatically inject `envoy` proxies into the `Executor` `Pods` as sidecar.