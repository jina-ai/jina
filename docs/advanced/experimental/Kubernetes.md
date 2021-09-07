# Jina on Kubernetes

Deploy your `Flow` on `Kubernetes`.
## Requirements
Please setup a `Kubernetes` cluster and pull the credentials. e.g.:

-  [minikube](https://minikube.sigs.k8s.io/docs/start/) (testing),
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine),
- [Amazon EKS](https://aws.amazon.com/eks),
- [Azure Kubernetes Service](https://azure.microsoft.com/en-us/services/kubernetes-service),
- [Digital Ocean](https://www.digitalocean.com/products/kubernetes/)
  
## Deploy your `Flow`
To deploy a `Flow` on `Kubernetes`, you have to set the `infrastructure='K8S'` when creating the `Flow`.
Call `flow.start()` to trigger the deployment. Make sure all `Executors` are containerized.

## Example
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

Deploy the search `Flow` on `Kubernetes`:
```python
from jina import Flow

shards = 3

flow = Flow(
    name='search-flow', port_expose=8080, infrastructure='K8S', protocol='http'
).add(
    # name of the service and deployment in Kubernetes
    name='test_searcher',

    # There will be 3 deployments and services with 2 replicas each.
    # In addition, there is a head and tail deployed
    # (distribute the request and collect the results)
    #
    #        shard0_replica0, shard0_replica1
    #      /                                  \
    # head - shard1_replica0, shard1_replica1 - tail
    #      \                                  /
    #        shard2_replica0, shard2_replica1
    #
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
  We recommend using a proxy based loadbalancing via `envoy`.
  Please inject the `envoy` proxy yourself for now.
  You can use the service mesh `Istio` to automatically inject `envoy` proxies into the `Executor` `Pods` as sidecar.