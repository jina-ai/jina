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
The context manager makes sure to deploy the `Flow` when entering the context and to clean it up when leaving the context.

```{caution}
All Executors in the Flow should be used with `jinahub+docker://...` or `docker://...`.
```

## Examples

### CLIP image encoder

The following code deploys a simple `Flow` with just a single `Executor`.
It does the following:
- setting up a port forward when entering the context of the `Flow`
- sending an example image to the `Flow`
- printing the dimension of the resulting embedding
- cleaning up the deployment when leaving the context of the `Flow`

```python
import numpy as np
from jina import Flow, Document

f = Flow(name='example-clip', port_expose=8080, infrastructure='K8S', protocol='http').add(
    uses='jinahub+docker://CLIPImageEncoder'
)

with f:
    resp = f.index(Document(id=f'image', blob=np.random.rand(3, 16, 16)), return_results=True)
    print('embedding size: ', len(resp[0].docs[0].embedding))
```
Console output:
```txt
create_example-clip@15611[I]:🏝️	Create Namespace "example-clip"
⠸ 0/2 waiting executor0 gateway to be ready...waiting_for_gateway@15611[L]: gateway has all its replicas ready!!
⠋ 1/2 waiting executor0 to be ready...waiting_for_executor0@15611[L]: executor0 has all its replicas ready!!
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
UserWarning: ignored unknown argument: ['8080']. (raised from /Users/florianhonicke/jina/jina/jina/helper.py:685)
embedding size:  512                                                                                       
```


### Postgres indexer

This example deploys and index `Flow` and a search `Flow` on `Kubernetes`.
Having two flows deployed independently allows query while indexing.
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

#### Indexing

```python
from jina import Flow, Document
import os
import numpy as np

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
    print('start indexing')
    f.post(
        '/index',
        [Document(id=f'item {i}', embedding=np.random.rand(128)) for i in range(100)],
    )
    print('indexing done')
```

Console output:
```txt
create_index-flow@19114[I]:🏝️	Create Namespace "index-flow"
⠸ 0/2 waiting test_searcher gateway to be ready...waiting_for_gateway@19114[L]: gateway has all its replicas ready!!
⠦ 1/2 waiting test_searcher to be ready...waiting_for_test_searcher@19114[L]: test_searcher has all its replicas ready!!
start indexing
UserWarning: ignored unknown argument: ['8080']. (raised from /Users/florianhonicke/jina/jina/jina/helper.py:685)
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
indexing done
  close_gateway@19114[L]: Successful deletion of deployment gateway
close_test_searcher@19114[L]: Successful deletion of deployment test_searcher
```

#### Searching

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
from jina import Flow, Document
import os
import numpy as np

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
    resp = f.post('/search', Document(embedding=np.random.rand(128)), return_results=True)
    print(f"Len response matches: {len(resp[0].docs[0].matches)}")
```
Console output:
```txt
create_search-flow2@19273[I]:🏝️	Create Namespace "search-flow2"
           JINA@19273[W]:🔁	roles.rbac.authorization.k8s.io "connection-pool" already exists
           JINA@19273[W]:🔁	rolebindings.rbac.authorization.k8s.io "connection-pool-binding" already exists
           JINA@19273[W]:🔁	roles.rbac.authorization.k8s.io "connection-pool" already exists
           JINA@19273[W]:🔁	rolebindings.rbac.authorization.k8s.io "connection-pool-binding" already exists
           JINA@19273[W]:🔁	roles.rbac.authorization.k8s.io "connection-pool" already exists
           JINA@19273[W]:🔁	rolebindings.rbac.authorization.k8s.io "connection-pool-binding" already exists
           JINA@19273[W]:🔁	roles.rbac.authorization.k8s.io "connection-pool" already exists
           JINA@19273[W]:🔁	rolebindings.rbac.authorization.k8s.io "connection-pool-binding" already exists
           JINA@19273[W]:🔁	roles.rbac.authorization.k8s.io "connection-pool" already exists
           JINA@19273[W]:🔁	rolebindings.rbac.authorization.k8s.io "connection-pool-binding" already exists
⠋ 0/2 waiting test_searcher gateway to be ready...waiting_for_test_searcher-head@19273[L]: test_searcher-head has all its replicas ready!!
⠋ 0/2 waiting test_searcher gateway to be ready...waiting_for_test_searcher-0@19273[L]: test_searcher-0 has all its replicas ready!!
⠦ 0/2 waiting test_searcher gateway to be ready...waiting_for_test_searcher-1@19273[L]: test_searcher-1 has all its replicas ready!!
⠇ 0/2 waiting test_searcher gateway to be ready...waiting_for_test_searcher-2@19273[L]: test_searcher-2 has all its replicas ready!!
⠙ 0/2 waiting test_searcher gateway to be ready...waiting_for_test_searcher-tail@19273[L]: test_searcher-tail has all its replicas ready!!
⠹ 1/2 waiting gateway to be ready...waiting_for_gateway@19273[L]: gateway has all its replicas ready!!
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
UserWarning: ignored unknown argument: ['8080']. (raised from /Users/florianhonicke/jina/jina/jina/helper.py:685)
Len response matches: 15
  close_gateway@19273[L]: Successful deletion of deployment gateway
close_test_searcher-head@19273[L]: Successful deletion of deployment test_searcher-head
close_test_searcher-0@19273[L]: Successful deletion of deployment test_searcher-0
close_test_searcher-1@19273[L]: Successful deletion of deployment test_searcher-1
close_test_searcher-2@19273[L]: Successful deletion of deployment test_searcher-2
close_test_searcher-tail@19273[L]: Successful deletion of deployment test_searcher-tail
```

## Scaling Executors on Kubernetes

In Jina we support two ways of scaling:
- **Replicas** can be used with any Executor type and is typically used for performance and availability.
- **Shards** are used for partitioning data and should only be used with Indexers since they store a state.

Check {ref}`here <flow-topology>` for more information.

Jina creates a separate Deployment in Kubernetes per Shard and uses [Kubernetes native replica scaling](https://kubernetes.io/docs/tutorials/kubernetes-basics/scale/scale-intro/) to create multiple Replicas per Shard.

