(flow-complex-topologies)=
# Topology

{class}`~jina.Flow`s are not restricted to sequential execution. Internally they are modeled as graphs, so they can represent any complex, non-cyclic topology.
A typical use case for such a Flow is a topology with a common pre-processing part, but different indexers separating embeddings and data.
To define a custom topology you can use the `needs` keyword when adding an {class}`~jina.Executor`. By default, a Flow assumes that every Executor needs the previously added Executor.

```python
from jina import Executor, Flow, requests, Document, DocumentArray


class FooExecutor(Executor):
    @requests
    async def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'foo was here and got {len(docs)} document'))


class BarExecutor(Executor):
    @requests
    async def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'bar was here and got {len(docs)} document'))


class BazExecutor(Executor):
    @requests
    async def baz(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'baz was here and got {len(docs)} document'))


f = (
    Flow()
    .add(uses=FooExecutor, name='fooExecutor')
    .add(uses=BarExecutor, name='barExecutor', needs='fooExecutor')
    .add(uses=BazExecutor, name='bazExecutor', needs='fooExecutor')
    .add(needs=['barExecutor', 'bazExecutor'])
)

with f:  # Using it as a Context Manager starts the Flow
    response = f.post(
        on='/search'
    )  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```

```{figure} needs-flow.svg
:width: 70%
:align: center
Complex Flow where one Executor requires two Executors to process Documents beforehand
```

This gives the output:

```text
['foo was here and got 0 document', 'bar was here and got 1 document', 'baz was here and got 1 document']
```

Both `BarExecutor` and `BazExecutor` only received a single `Document` from `FooExecutor` because they are run in parallel. The last Executor `executor3` receives both DocumentArrays and merges them automatically.
This automated merging can be disabled with `no_reduce=True`. This is useful for providing custom merge logic in a separate Executor. In this case the last `.add()` call would look like `.add(needs=['barExecutor', 'bazExecutor'], uses=CustomMergeExecutor, no_reduce=True)`. This feature requires Jina >= 3.0.2.

(replicate-executors)=
## Replicate Executors

Replication creates multiple copies of the same {class}`~jina.Executor`. Each request in the {class}`~jina.Flow` is then passed to only one replica (instance) of that Executor. This is useful for performance and availability:
* If you have slow Executors (like some Encoders) you can scale up the number of instances to process multiple requests in parallel.
* Executors might need to be taken offline occasionally (for updates, failures, etc.), but you may want your Flow to be able to process requests without downtime. Using Replicas, any single replica of an Executor can be taken offline as long as there is still at least one running online. This ensures high availability for your Flow.

```python
from jina import Flow

f = Flow().add(name='slow_encoder', replicas=3).add(name='fast_indexer')
```

```{figure} replicas-flow.svg
:width: 70%
:align: center
Flow with three replicas of slow_encoder and one replica of fast_indexer
```

The above Flow creates a topology with three replicas of the Executor `slow_encoder`. The `Flow` sends every 
request to exactly one of the three instances. Then the replica sends its result to `fast_indexer`.

## Replicate on multiple GPUs

To replicate your {class}`~jina.Executor`s so that each replica uses a different GPU on your machine, you can tell the {class}`~jina.Flow` to use multiple GPUs by passing `CUDA_VISIBLE_DEVICES=RR` as an environment variable.
The Flow then assigns each available GPU to replicas in a round-robin fashion.

```{caution} 
You should only replicate on multiple GPUs with `CUDA_VISIBLE_DEVICES=RR` locally.  
```

```{tip}
In Kubernetes or with Docker Compose you should allocate GPU resources to each replica directly in the configuration files.
```

For example, if you have three GPUs and one of your Executor has five replicas then:

````{tab} Python
 In a `flow.py` file 
```python
from jina import Flow

with Flow().add(
    uses='jinahub://CLIPEncoder', replicas=5, install_requirements=True
) as f:
    f.block()
```

```shell
CUDA_VISIBLE_DEVICES=RR python flow.py
```
````

````{tab} YAML
In a `flow.yaml` file
```yaml
jtype: Flow
executors:
- uses: jinahub://CLIPEncoder
  install_requirements: True
  replicas: 5  
```

```shell
CUDA_VISIBLE_DEVICES=RR jina flow --uses flow.yaml
```
````

The Flow assigns GPU devices in the following round-robin fashion:

| GPU device | Replica ID |
|------------|------------|
| 0          | 0          |
| 1          | 1          |
| 2          | 2          |
| 0          | 3          |
| 1          | 4          |

 
You can restrict the visible devices in round-robin assignment using `CUDA_VISIBLE_DEVICES=RR0:2`, where `0:2` corresponds to a Python slice. This creates the following assignment:

| GPU device | Replica ID |
|------------|------------|
| 0          | 0          |
| 1          | 1          |
| 0          | 2          |
| 1          | 3          |
| 0          | 4          |


You can restrict the visible devices in round-robin assignment by assigning the list of device IDs to `CUDA_VISIBLE_DEVICES=RR1,3`. This creates the following assignment:

| GPU device | Replica ID |
|------------|------------|
| 1          | 0          |
| 3          | 1          |
| 1          | 2          |
| 3          | 3          |
| 1          | 4          |

You can also refer to GPUs by their UUID. For instance, you could assign a list of device UUIDs `CUDA_VISIBLE_DEVICES=RRGPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5,GPU-0bbbbbbb-74d2-7297-d557-12771b6a79d5,GPU-0ccccccc-74d2-7297-d557-12771b6a79d5,GPU-0ddddddd-74d2-7297-d557-12771b6a79d5`.
Check [CUDA Documentation](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#env-vars) to see the accepted formats to assign CUDA devices by UUID.

| GPU device | Replica ID |
|------------|------------|
| GPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5          | 0          |
| GPU-0bbbbbbb-74d2-7297-d557-12771b6a79d5          | 1          |
| GPU-0ccccccc-74d2-7297-d557-12771b6a79d5          | 2          |
| GPU-0ddddddd-74d2-7297-d557-12771b6a79d5          | 3          |
| GPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5          | 4          |

## Distributed replicas

You can run replicas of the same Executor on different machines.

To add distributed replicas to a Flow, the Executor replicas must already be running on their respective machines.

````{admonition} External Executors
:class: seealso
To start Executors outside a Flow, see our {ref}`how-to on external Executors <external-executor>`.
````

Then, you can add them by specifying their hosts, ports, and `external=True`:

```python
from jina import Flow

Flow().add(host='localhost:1234,91.198.174.192:12346', external=True)
```

This connects to `grpc://localhost:12345` and `grpc://91.198.174.192:12346` as two replicas of the same Executor.


(partition-data-by-using-shards)=
## Partition data with shards

Sharding partitions data (like an index) into several parts. This distributes the data across multiple machines.
This is helpful when:

- The full data does not fit on one machine. 
- The latency of a single request becomes too large.

In these cases splitting the load across two or more machines yields better results.

For shards, you can define which shard (instance) receives the request from its predecessor. This behaviour is called `polling`. `ANY` means only one shard receives a request, while  `ALL` means that all shards receive a request.
Polling can be configured per endpoint (like `/index`) and {class}`~jina.Executor`.
By default the following `polling` is applied:
- `ANY` for endpoints at `/index`
- `ALL` for endpoints at `/search`
- `ANY` for all other endpoints

When you shard your index, the request handling usually differs between index and search requests:

- Index (and update, delete) are handled by a single shard => `polling='any'`
- Search requests are handled by all shards => `polling='all'`

For indexing, you only want a single shard to receive a request, because this is sufficient to add it to the index.
For searching, you probably need to send the search request to all shards, because the requested data could be on any shard.

```python Usage
from jina import Flow

flow = Flow().add(name='ExecutorWithShards', shards=3, polling={'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'})
```

The above example results in a {class}`~jina.Flow` having the Executor `ExecutorWithShards` with the following polling options:
- `/index` has polling `ANY` (the default value is not changed here)
- `/search` has polling `ANY` as it is explicitly set (usually that should not be necessary)
- `/custom` has polling `ALL`
- All other endpoints have polling `ANY` due to using `*` as a wildcard to catch all other cases


(flow-filter)=
## Filter by condition

To define a filter condition, use [DocArrays rich query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions).
You can set a filter for each individual {class}`~jina.Executor`, and every Document that does not satisfy the filter condition is
removed before reaching that Executor.

To add a filter condition to an Executor, pass it to the `when` parameter of {meth}`~jina.Flow.add` method of the Flow.
This then defines *when* a document is processed by the Executor:

````{tab} Python

```{code-block} python
---
emphasize-lines: 4, 9
---

from jina import Flow, DocumentArray, Document

f = Flow().add().add(when={'tags__key': {'$eq': 5}})  # Create the empty Flow, add condition

with f:  # Using it as a Context Manager starts the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fulfilling the condition is processed and therefore returned.
```

```shell
[{'key': 5.0}]
```

````

````{tab} YAML
`flow.yml`:

```yaml
jtype: Flow
executors:
  - name: executor
    when:
        tags__key:
            $eq: 5
```

```{code-block} python
---
emphasize-lines: 9
---
from docarray import DocumentArray, Document
from jina import Flow

f = Flow.load_config('flow.yml')  # Load the Flow definition from Yaml file

with f:  # Using it as a Context Manager starts the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fulfilling the condition is processed and therefore returned.
```

```shell
[{'key': 5.0}]
```
````

Note that if a Document does not satisfy the `when` condition of a filter, the filter removes the Document *for the entire branch of the Flow*.
This means that every Executor located behind a filter is affected by this, not just the specific Executor that defines the condition.
As with a real-life filter, once something fails to pass through it, it no longer continues down the pipeline.

Naturally, parallel branches in a Flow do not affect each other. So if a Document gets filtered out in only one branch, it can
still be used in the other branch, and also after the branches are re-joined:

````{tab} Parallel Executors

```{code-block} python
---
emphasize-lines: 7, 8, 21
---

from jina import Flow, DocumentArray, Document

f = (
    Flow()
    .add(name='first')
    .add(when={'tags__key': {'$eq': 5}}, needs='first', name='exec1')
    .add(when={'tags__key': {'$eq': 4}}, needs='first', name='exec2')
    .needs_all(name='join')
)  # Create Flow with parallel Executors

#                                   exec1
#                                 /      \
# Flow topology: Gateway --> first        join --> Gateway
#                                 \      /
#                                  exec2

with f:
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(ret[:, 'tags'])  # Each Document satisfies one parallel branch/filter
```

```shell
[{'key': 5.0}, {'key': 4.0}]
```

````

````{tab} Sequential Executors
```{code-block} python
---
emphasize-lines: 7, 8, 21
---

from jina import Flow, DocumentArray, Document

f = (
    Flow()
    .add(name='first')
    .add(when={'tags__key': {'$eq': 5}}, name='exec1', needs='first')
    .add(when={'tags__key': {'$eq': 4}}, needs='exec1', name='exec2)
)  # Create Flow with sequential Executors

# Flow topology: Gateway --> first --> exec1 --> exec2 --> Gateway

with f:
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(ret[:, 'tags'])  # No Document satisfies both sequential filters
```

```shell
[]
```
````

This feature is useful to prevent some specialized Executors from processing certain Documents.
It can also be used to build *switch-like nodes*, where some Documents pass through one branch of the Flow,
while other Documents pass through a different parallel branch.

Note that whenever a Document does not satisfy the condition of an Executor, it is not even sent to that Executor.
Instead, only a lightweight Request without any payload is transferred.
This means that you can not only use this feature to build complex logic, but also to minimize your networking overhead.

````{admonition} See Also
:class: seealso

For a hands-on example of leveraging filter conditions, see {ref}`this how-to <flow-switch>`.
````
