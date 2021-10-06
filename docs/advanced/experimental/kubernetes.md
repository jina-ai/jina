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
```

## Scaling Executors on Kubernetes

In Jina we support two ways of scaling:
- **Replicas** can be used with any Executor type.
- **Shards** should only be used with Indexers, since they store a state.

Check {ref}`here <flow-parallelization>` for more information.

```{admonition} Important
:class: important
This page describes Jina's behavior with kubernetes deployment for now.
When using `shards` and `replicas` without kubernetes, Jina will behave slightly different.
It is discouraged to use the `parallel` argument when deploying to kubernetes.
```

(replicas)=
### Replicas

Replication (or horizontal scaling) means duplicating an Executor and its state.
It allows more requests to be served in parallel.
A single request to Jina is only send to one of the replicas.
Furthermore, it increases the failure tolerance.
When one replica dies, another will immediately take over.
In a cloud environment any machine might die at any point in time.
Thus, using replicas is important for reliable services.
Replicas are currently only supported, when deploying Jina with kubernetes.

```python Usage
from jina import Flow

f = Flow().add(name='ExecutorWithReplicas', replicas=3)
```

(shards)=
### Shards

Sharding means splitting the content of an Indexer into several parts.
These parts are then put on different machines.
This is helpful in two situations:

- When the full data does not fit on one machine 
- When the latency of a single request becomes too large.

Then splitting the load across two or more machines yields better results.

When you shard your index, the request handling usually differs between index and search requests:

- Index (and update, delete) will just be handled by a single shard => `polling='any'`
- Search requests are handled by all shards => `polling='all'`

```python Usage
from jina import Flow

index_flow = Flow().add(name='ExecutorWithShards', shards=3, polling='any')
search_flow = Flow().add(name='ExecutorWithShards', shards=3, polling='all', uses_after='MatchMerger')
```

### Merging search results via `uses_after`

Each shard of a search Flow returns one set of results for each query Document.
A merger Executor combines them afterwards.
You can use the pre-built [MatchMerger](https://hub.jina.ai/executor/mruax3k7) or define your own merger.

```{admonition} Example
:class: example
A search Flow has 10 shards for an Indexer.
Each shard returns the top 20 results.
After the merger there will be 200 results per query Document.
```

## Combining replicas & shards

Combining both gives all the advantages mentioned above.
When deploying to kubernetes, Jina replicates each single shard.
Thus, shards can scale independently.
The data synchronisation across replicas must be handled by the respective Indexer.
For more detailed see {ref}`Dump and rolling update <dump-rolling-restart>`.

