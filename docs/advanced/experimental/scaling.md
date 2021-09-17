# Scaling Executors in kubernetes

In Jina we support to ways of scaling:
- *Replicas* can be used with any Executor type.
- *Shards* should only be used with Indexers, since they store a state.

```{admonition} Important
:class: important
This page describes Jinas behavior with kubernetes deployment for now.
When using `shards` and `replicas` without kubernetes, Jina will behave slightly different.
It is discouraged to use the `parallel` argument, when deploying to kubernetes.
```

(replicas)=
## Replicas

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
## Shards

Sharding means splitting the content of an Indexer into several parts.
These parts are then put on different machines.
This is helpful, in two situations:

- When the full data does not fit onto one machine.
- When the latency of a single request becomes to slow.
  Then two machines can compute the result faster.

When you shard your index, the request handling usually differes for index and search requests:

- Index (and update, delete) will just be handled by a single shard.
- Search requests are handled by all shards.

```python Usage
from jina import Flow

f = Flow().add(name='ExecutorWithShards', shards=3)
```

## Combining Replicas & Shards

Combining both gives all above mentioned advantages.
When deploying to kubernetes, Jina replicates is applied on each single shard.
Thus, shards can scale independently.
The data syncronisation across replicas must be handled by the respective Indexer.
For more detailed see {doc}`Dump and rolling update <./indexers/dump-rolling-update>`.
