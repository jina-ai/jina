(flow-topology)=
# Distributed & Parallel Execution

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

```{figure} simple-flow.svg
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
### Merging results
In the previous Flow, each of the Executors `p1`, `p2` and `p3` work in parallel and generate one set of results.
If you have an Executor that depends on all of them like `r1`, you might need to have all 3 results combined into one 
DocumentArray in the next steps. Let's suppose the following concrete example:
* The Documents you sent are images containing some text.
* `p1` fills the `embedding` attribute of Documents using an encoder model.
* `p2` segments further the image into smaller chunks of images.
* `p3` extracts the text and adds them as chunks.

We need to end up with Documents that contain all this new data. Well, by default, if you have a pod that needs all 3 
Executors (`p1`, `p2` and `p3`), this happens with our default `Reduce` logic.

````{admonition} See Also
:class: seealso

Read more about {ref}`how Reducing works <reduce>`.
````

If you don't want to use the default `Reduce` logic, you can implement a custom reducing logic in an Executor and 
specify it with `uses` or `uses_before`:

```python
import itertools
from jina import Executor, requests, Flow, DocumentArray
from typing import List


class CustomReducerExecutor(Executor):
    @requests
    def reduce(self, docs_matrix: List['DocumentArray'] = [], **kwargs):
        # simply chain all DocumentArrays
        return DocumentArray(itertools.chain.from_iterable(docs_matrix))

f = (Flow()
     .add(name='p1', needs='gateway')
     .add(name='p2', needs='gateway')
     .add(name='p3', needs='gateway')
     .needs(['p1', 'p2', 'p3'], name='r1', uses=CustomReducerExecutor))
```

````{admonition} Note
:class: note
If there is no pod that needs all 3 pods `p1`, `p2` and `p3`, there will be no reduce logic.
If you want to add a pod that needs all of them but you don't want to have any reducing, use `uses='BaseExecutor'`.
````


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

The above Flow will create a topology with three Replicas of Executor `slow_encoder`. The `Gateway` will send every 
request to exactly one of the three instances. Then the replica will send its result to `fast_indexer`.

### Avoiding Bottlenecks on Executors with `replicas`
In this section, we will showcase how we can avoid having bottlenecks on slow Executors by using `replicas`.

Suppose we have the following Executor:

```python
import time
from jina import Executor, requests


class MyExecutor(Executor):

    @requests(on='/slow')
    def foo(self, **kwargs):
        time.sleep(5)

    @requests(on='/fast')
    def bar(self, **kwargs):
        pass
```

We will simulate parallel requests to both endpoints of the Executor with these utility functions:

```python
from jina.logging.profile import TimeContext
from jina import Client
import multiprocessing

def make_request(endpoint):
    with TimeContext(f'calling {endpoint} roundtrip'):
        c = Client(protocol='grpc', port=12345)
        c.post(endpoint)


def simulate(flow):
    with flow:
        mp = []
        
        # make multiple requests to both endpoints, in parallel
        for endpoint in ['/slow', '/fast', '/slow', '/fast']:
            p = multiprocessing.Process(target=make_request, args=(endpoint,))
            p.start()
            mp.append(p)

        # 
        for p in mp:
            p.join()
```

If we simply create a Flow with only 1 instance of `MyExecutor`, requests to the slow endpoint will make a bottleneck. 
However, creating replicas will unblock the Flow:

````{tab} with replicas
```python
from jina import Flow

scaled_f = Flow(protocol='grpc', port_expose=12345).add(uses=MyExecutor, replicas=2)

with TimeContext('calling scaled flow'):
    simulate(scaled_f)  # will take around 5 seconds
```

```text
calling scaled flow takes 6 seconds (6.11s)
```
````

````{tab} without replicas
```python
from jina import Flow

f = Flow(protocol='grpc', port_expose=12345).add(uses=MyExecutor)

with TimeContext('calling normal flow'):
    simulate(f)  # will take around 10 seconds
```

```text
calling normal flow takes 11 seconds (11.75s)
```
````
Therefore, by using `replicas`, the Flow enjoys a non-blocking behavior and we can avoid bottlenecks.

````{admonition} Important
:class: important
By default, `polling='ANY'`. If `polling` is set to `ALL`, this will not be valid anymore: All instances of the 
Executor will receive each request and there will be no performance benefits.
````

## Partition data by using Shards

Shards can be used to partition data (like an Index) into several parts. This enables the distribution of data across multiple machines.
This is helpful in two situations:

- When the full data does not fit on one machine 
- When the latency of a single request becomes too large.

Then splitting the load across two or more machines yields better results.

For Shards, you can define which shard (instance) will receive the request from its predecessor. This behaviour is called `polling`. `ANY` means only one shard will receive a request and `ALL` means that all Shards will receive a request.
Polling can be configured per endpoint (like `/index`) and Executor.
By default the following `polling` is applied:
- `ANY` for endpoints at `/index`
- `ALL` for endpoints at `/search`
- `ANY` for all other endpoints

When you shard your index, the request handling usually differs between index and search requests:

- Index (and update, delete) will just be handled by a single shard => `polling='any'`
- Search requests are handled by all Shards => `polling='all'`

For indexing, you only want a single shard to receive a request, because this is sufficient to add it to the index.
For searching, you probably need to send the search request to all Shards, because the requested data could be on any shard.

```python Usage
from jina import Flow

flow = Flow().add(name='ExecutorWithShards', shards=3, polling={'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'})
```

The example above will result in a Flow having the Executor `ExecutorWithShards` with the following polling options configured
- `/index` has polling `ANY` (the default value is not changed here)
- `/search` has polling `ANY` as it is explicitly set (usually that should not be necessary)
- `/custom` has polling `ALL`
- all other endpoints will have polling `ANY` due to the usage of `*` as a wildcard to catch all other cases



### Merging search results

Each shard of a search Flow returns one set of results for each query Document.
By default, these different results will be combined into one DocumentArray using our default `Reduce` logic.

````{admonition} See Also
:class: seealso

Read more about {ref}`how Reducing works`.
````

You can customize the reduce logic and specify a different Reducer Executor with parameter `uses_after`.
For example, you can use the pre-built [MatchMerger](https://hub.jina.ai/executor/mruax3k7) or define your merger.

```{admonition} Example
:class: example
A search Flow has 10 Shards for an Indexer.
Each shard returns the top 20 results.
After the merger there will be 200 results per query Document.
```

````{tab} Default Reduce
```{code-block} python
from jina import Flow
search_flow = Flow().add(name='ExecutorWithShards', shards=3, polling='all')
```
````

````{tab} Custom Reduce with MatchMerger
```{code-block} python
from jina import Flow
search_flow = Flow().add(name='ExecutorWithShards', shards=3, polling='all', uses_after='jinahub://MatchMerger')
```
````

````{admonition} Warning
:class: warning
The default Reduce logic does not keep the matches sorted when combining them. If you wish to have sorted matches, you 
should add an Executor to sort the matches.
````


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

## Replicas vs Shards

The next table shows the difference between shards and replicas.

||Replicas|Shards|
|---|---|---|
|Create multiple copies of an executor| ✅ | ✅ |
|Partition data into several parts | ❌ | ✅ |
|Request handled by one of the executors | ✅ | ✅, if `polling = 'any'` |
|Request handled by all of the executors | ❌ | ✅, if `polling = 'all'` |

Think of using `replicas` when you have slow Executors and you want to be able to process multiple requests in parallel. 
Also replicas provide high availability in case some executors are taken down (for updates, failures, etc)

On the other hand, when your data  is too large to fit in one machine or if the latency of a request is too large `shards` is your best option since it allows you to split your data across multiple machines.

````{admonition} Warning
:class: warning
Sometimes you'll also encouter `parallel`, this is equivalent to `shards` and is only kept for backwards compatibility.
````

(reduce)=
## Reducing
Reducing is a mechanism that applies by default to DocumentArrays resulted by instances of Executors running in 
parallel in a Flow. It combines the multiple DocumentArrays into one DocumentArray when you have one of these 2 cases:
* Your Flow contains 2 or more shards of the same Executor with `polling='all'`
* Your Flow contains 2 or more different Executors running in parallel and you have another Executor that needs 2 or 
more of them.
Reducing is necessary if your Flow needs the combined DocumentArray in later steps.

Reduction consists in reducing all DocumentArrays sequentially using [DocumentArray.reduce](https://docs.jina.ai/api/jina.types.arrays.mixins.reduce/?highlight=reduce#jina.types.arrays.mixins.reduce.ReduceMixin.reduce).
The resulting DocumentArray contains Documents of all DocumentArrays.

If a Document exists in many DocumentArrays, data properties are merged.

Matches and chunks of a Document belonging to many DocumentArrays are also reduced in the same way.
Other non-data properties are ignored.

````{admonition} Warning
:class: warning
If a data property is set on many Documents with the same ID, only one value is kept in the final Document. This value 
can be belong to any of these Documents. This also means, if you make the same request, with such conflicting data 
properties, you can end up with undeterministic results.
When you use shards or parallel branches, you should always make sure that all data properties of the same Documents 
either do not conflict or have the same value.
````