(kubernetes)=
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
Console output:
```txt
start_executor0@65952[I]:🏝️	Create Namespace "index-flow" for "executor0"
deploy_executor0@65952[I]:🔋	Create Service for "executor0" with exposed port "8080"
deploy_executor0@65952[I]:🐳	Create Deployment for "executor0" with image "jinahub/0hnlmu3q:v33-2.1.0", replicas 1 and init_container False
  start_gateway@65952[I]:🏝️	Create Namespace "index-flow" for "gateway"
  start_gateway@65952[I]:🔁	namespaces "index-flow" already exists
 deploy_gateway@65952[I]:🔋	Create Service for "gateway" with exposed port "8080"
 deploy_gateway@65952[I]:🐳	Create Deployment for "gateway" with image "jinaai/jina:master-py38-standard", replicas 1 and init_container False                                                                                               
```

After the deployment finished, set up port forwarding to enable the client to send requests to the `Flow`.

```bash
kubectl port-forward svc/gateway -n index-flow 8080:8080
```

Console output:
```txt
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
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

print('embedding size: ', len(embedding))
```

Console output:
```txt
embedding size:  512
```

#### Cleanup
```bash
kubectl delete ns index-flow
```

Console output:
```txt
namespace "index-flow" deleted
```


### Postgres indexer

This example deploys the index `Flow` on `Kubernetes`
You can use any `postgres` database which is reachable from within the `Kubernetes` cluster.
Here is an example on how to create a `postgres` database on the cluster directly:
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-release bitnami/postgresql
```
You can get the password like this:
```bash
export POSTGRES_PASSWORD=$(kubectl get secret --namespace default my-release-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)
```

#### Index flow

```python
from jina import Flow
import os

f = Flow(
    name='index-flow', port_expose=8080, infrastructure='K8S', protocol='http'
).add(
    # name of the service and deployment in Kubernetes
    name='test_searcher',
    # executor has to be containerized
    uses='jinahub+docker://FaissPostgresIndexer',
    # database configuration
    uses_with={
        'hostname': f'my-release-postgresql.default.svc.cluster.local',
        'username': 'postgres',
        'password': os.environ['POSTGRES_PASSWORD'],
        'database': 'postgres',
        'table': 'test_searcher',
    },
)

with f:
    f.block()
```

Console output:
```txt
start_test_searcher@80992[I]:🏝️	Create Namespace "index-flow" for "test_searcher"
deploy_test_searcher@80992[I]:🔋	Create Service for "test-searcher" with exposed port "8080"
deploy_test_searcher@80992[I]:🐳	Create Deployment for "test-searcher" with image "jinahub/nflcyqe2:v10-2.1.0", replicas 1 and init_container False
  start_gateway@80992[I]:🏝️	Create Namespace "index-flow" for "gateway"
  start_gateway@80992[I]:🔁	namespaces "index-flow" already exists
 deploy_gateway@80992[I]:🔋	Create Service for "gateway" with exposed port "8080"
 deploy_gateway@80992[I]:🐳	Create Deployment for "gateway" with image "jinaai/jina:2.1.4-py38-standard", replicas 1 and init_container False
```

Use `port-forward` to send requests to the gateway of the index `Flow`:

```bash
kubectl port-forward svc/gateway -n index-flow 8080:8080
```

Console output:
```txt
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080

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

Console output:
```txt
index document: item 0
{"requestId":"a133c678-99cc-4903-ae34-1524d3fb3cc4",...}
index document: item 1
...
index document: item 99
{"requestId":"02a9041b-d5e8-4625-8e97-6dffb5da2e96",...}
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
import os

shards = 3

f = Flow(
    name='search-flow', port_expose=8080, infrastructure='K8S', protocol='http'
).add(
    # name of the service and deployment in Kubernetes
    name='test_searcher',
    shards=shards,
    replicas=2,
    uses='jinahub+docker://FaissPostgresIndexer',
    uses_with={
        'startup_sync_args': {'only_delta': True},
        'total_shards': shards,
        'hostname': f'my-release-postgresql.default.svc.cluster.local',
        'username': 'postgres',
        'password': os.environ['POSTGRES_PASSWORD'],
        'database': 'postgres',
        'table': 'test_searcher',
    },
    uses_after='jinahub+docker://MatchMerger',
)

with f:
    f.block()
```
Console output:
```txt
start_test_searcher@81116[I]:🏝️	Create Namespace "search-flow" for "test_searcher"
deploy_test_searcher@81116[I]:🔋	Create Service for "test-searcher-head" with exposed port "8080"
deploy_test_searcher@81116[I]:🐳	Create Deployment for "test-searcher-head" with image "jinaai/jina:2.1.4-py38-standard", replicas 1 and init_container False
deploy_test_searcher@81116[I]:🔋	Create Service for "test-searcher-0" with exposed port "8080"
deploy_test_searcher@81116[I]:🐳	Create Deployment for "test-searcher-0" with image "jinahub/nflcyqe2:v10-2.1.0", replicas 2 and init_container False
deploy_test_searcher@81116[I]:🔋	Create Service for "test-searcher-1" with exposed port "8080"
deploy_test_searcher@81116[I]:🐳	Create Deployment for "test-searcher-1" with image "jinahub/nflcyqe2:v10-2.1.0", replicas 2 and init_container False
deploy_test_searcher@81116[I]:🔋	Create Service for "test-searcher-2" with exposed port "8080"
deploy_test_searcher@81116[I]:🐳	Create Deployment for "test-searcher-2" with image "jinahub/nflcyqe2:v10-2.1.0", replicas 2 and init_container False
deploy_test_searcher@81116[I]:🔋	Create Service for "test-searcher-tail" with exposed port "8080"
deploy_test_searcher@81116[I]:🐳	Create Deployment for "test-searcher-tail" with image "jinahub/mruax3k7:v6-2.1.0", replicas 1 and init_container False
  start_gateway@81116[I]:🏝️	Create Namespace "search-flow" for "gateway"
  start_gateway@81116[I]:🔁	namespaces "search-flow" already exists
 deploy_gateway@81116[I]:🔋	Create Service for "gateway" with exposed port "8080"
 deploy_gateway@81116[I]:🐳	Create Deployment for "gateway" with image "jinaai/jina:2.1.4-py38-standard", replicas 1 and init_container False                                                                                                 
```

Use `port-forward` to send requests to the gateway of the search `Flow`:

```bash
kubectl port-forward svc/gateway -n search-flow 8081:8080
```
Console output:
```txt
Forwarding from 127.0.0.1:8081 -> 8080
Forwarding from [::1]:8081 -> 8080
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

Console output:
```txt
Len response matches: 15
```

```{admonition} Limitations of the Current Implemenation
:class: caution

- each `Executor` has to be containerized
- only stateless executors are supported when using replicas > 1
```

## Scaling Executors on Kubernetes

In Jina we support two ways of scaling:
- **Replicas** can be used with any Executor type and is typically used for performance and avaibility.
- **Shards** are used for partitioning data and should only be used with Indexers, since they store a state.

Check {ref}`here <flow-parallelization>` for more information.

Jina creates a separate Deployment in Kubernetes per Shard and uses [Kubernetes native replica scaling](https://kubernetes.io/docs/tutorials/kubernetes-basics/scale/scale-intro/) to create multiple Replicas per Shard.

