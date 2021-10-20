(flow-topology)=
# Topology

The topology of a Flow defines how information is distributed between all Executors.

Each Executor has predecessors and successors. An Executor receives requests from all of its predecessors and sends them to all of its successors.

Additionally, an Executor can be split into Shards and Replicas. This enables horizontal scaling of Executors. A shard is typically used for partitioning data (like a big index) and Replicas are used to increase throughput and availability.

## Define predecessors via `needs`

To define predecessors of an Executor, use the `needs` parameter. If `needs` is not provided, the previously added Executor is set as the default:

```python
from jina import Flow

f = (Flow()
     .add(name='p1', needs='gateway')
     .add(name='p2', needs='gateway')
     .add(name='p3', needs='gateway')
     .needs(['p1', 'p2', 'p3'], name='r1'))
```

```{figure} ../../../.github/simple-plot3.svg
:align: center
```

`p1`, `p2`, `p3` now subscribe to `Gateway` and conduct their work in parallel. The last `.needs()` blocks all Executors
until they finish their work.

`.needs()` is syntax sugar and roughly equal to:

```python
.add(needs=['p1', 'p2', 'p3'])
```

`.needs_all()` is syntax sugar and roughly equal to:

```python
.add(needs=[all_orphan_executors_so_far])
```

"Orphan" Executors have no connected Executors to their outputs. The above code snippet can be also written as:

```python
from jina import Flow

f = (Flow()
     .add(name='p1', needs='gateway')
     .add(name='p2', needs='gateway')
     .add(name='p3', needs='gateway')
     .needs_all())
```

## Scale Executors by using Replicas

Replicas can be used to create multiple copies of the same Executor. Each request in the Flow is then passed to only one replica (instance) of your Executor. This can be useful for a couple of challenges like performance and availability:
* If you have slow Executors (like some Encoders) you may want to scale up the number of instances of this particular Executor so that you can process multiple requests in parallel
* Executors might need to be taken offline from time to time (updates, failures, etc.), but you may want your Flow to be able to process requests all the time. In this case Replicas can be used as well so that any Replica of an Executor can be taken offline as long as there is still one running Replica online. Using this technique it is possible to create a High availability setup for your Flow.

```python
from jina import Flow

f = (Flow()
     .add(name='slow_encoder', replicas=3)
     .add(name='fast_indexer'))
```

```{figure} ../../../.github/2.0/parallel-explain.svg
:align: center
```

The above Flow will create a topology with three Replicas of Executor `slow_encoder`. The `Gateway` will send every request to exactly one of the three instances. Then the replica will send its result to `fast_indexer`.

## Partition data by using Shards

Shards can be used to partition data (like an Index) into several parts. This enables the distribution of data across multiple machines.
This is helpful in two situations:

- When the full data does not fit on one machine 
- When the latency of a single request becomes too large.

Then splitting the load across two or more machines yields better results.

For Shards, you can define which shard (instance) will receive the request from its predecessor. This behaviour is called `polling`. By default `polling` is set to `ANY`, which means only one shard will receive a request. If `polling` is to `ALL` it means that all Shards will receive a request.

When you shard your index, the request handling usually differs between index and search requests:

- Index (and update, delete) will just be handled by a single shard => `polling='any'`
- Search requests are handled by all Shards => `polling='all'`

For indexing, you only want a single shard to receive a request, because this is sufficient to add it to the index.
For searching, you probably need to send the search request to all Shards, because the requested data could be on any shard.

```python Usage
from jina import Flow

index_flow = Flow().add(name='ExecutorWithShards', shards=3, polling='any')
search_flow = Flow().add(name='ExecutorWithShards', shards=3, polling='all', uses_after='MatchMerger')
```

### Merging search results via `uses_after`

Each shard of a search Flow returns one set of results for each query Document.
A merger Executor combines them afterwards.
You can use the pre-built [MatchMerger](https://hub.jina.ai/executor/mruax3k7) or define your merger.

```{admonition} Example
:class: example
A search Flow has 10 Shards for an Indexer.
Each shard returns the top 20 results.
After the merger there will be 200 results per query Document.
```

## Combining Replicas & Shards

Replicas and Shards can also be combined, which is necessary for Flows with high scalability needs.
In this case Jina will shard the Executor and create Replicas for each shard.

```python
from jina import Flow

f = (Flow()
     .add(name='shards_with_replicas', shards=2, replicas=3))
```

```{figure} ../../../.github/2.0/replica_shards_example.svg
:align: center
```

This Flow has a single Executor with 2 Shards and 3 Replicas, which means it gets split into 2 Shards with 3 Replicas each. In total this Flow has 2*3=6 workers and could be distributed to six different machines if necessary.

## Replica vs Shards

The next table shows the difference between shards and replicas.

||Replica|Shards|
|---|---|---|
|Create multiple copies of an executor| ✅ | ✅ |
|Partition data into several parts | ❌ | ✅ |
|Request handeled by one of the executors | ✅ | ✅, if `polling = 'any'` |
|Request handeled by all of the executors | ❌ | ✅, if `polling = 'all'` |

Notes :
 - `parallel` is equivalent to `shards` , they both behave similarly (for backwards compatibility `parallel` is kept)  
 - You can combine `replica` and  `parallel` as well as `replica` and `shards`, this will behave like the example above. 
 - If you combine `parallel` and `shards` the latter argument will be used. In example :

```python
from jina import Flow

 f = (Flow()
     .add(name='shards_with_replicas', shards=2, parallel=3))
```     
In this case 3 shards will be created.