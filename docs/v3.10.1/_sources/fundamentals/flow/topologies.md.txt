(flow-complex-topologies)=
# Topology

{class}`~jina.Flow`s are not restricted to sequential execution. Internally they are modelled as graphs and as such can represent any complex, non-cyclic topology.
A typical use case for such a Flow is a topology with a common pre-processing part, but different indexers separating embeddings and data.
To define a custom Flow topology you can use the `needs` keyword when adding an {class}`~jina.Executor`. By default, a Flow assumes that every Executor needs the previously added Executor.

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

with f:  # Using it as a Context Manager will start the Flow
    response = f.post(
        on='/search'
    )  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```

```{figure} needs-flow.svg
:width: 70%
:align: center
Complex Flow where one Executor requires two Executors to process Documents before
```

This will get you the following output:

```text
['foo was here and got 0 document', 'bar was here and got 1 document', 'baz was here and got 1 document']
```

So both `BarExecutor` and `BazExecutor` only received a single `Document` from `FooExecutor` as they are run in parallel. The last Executor `executor3` will receive both DocumentArrays and merges them automatically.
The automated merging can be disabled by setting `disable_reduce=True`. This can be useful when you need to provide your custom merge logic in a separate Executor. In this case the last `.add()` call would like `.add(needs=['barExecutor', 'bazExecutor'], uses=CustomMergeExecutor, disable_reduce=True)`. This feature requires Jina >= 3.0.2.

(replicate-executors)=
## Replicate Executors

Replication can be used to create multiple copies of the same {class}`~jina.Executor`s. Each request in the {class}`~jina.Flow` is then passed to only one replica (instance) of your Executor. This can be useful for a couple of challenges like performance and availability:
* If you have slow Executors (like some Encoders) you may want to scale up the number of instances of this particular Executor so that you can process multiple requests in parallel
* Executors might need to be taken offline from time to time (updates, failures, etc.), but you may want your Flow to be able to process requests without downtimes. In this case Replicas can be used as well so that any Replica of an Executor can be taken offline as long as there is still one running Replica online. Using this technique it is possible to create a High availability setup for your Flow.

```python
from jina import Flow

f = Flow().add(name='slow_encoder', replicas=3).add(name='fast_indexer')
```

```{figure} replicas-flow.svg
:width: 70%
:align: center
Flow with 3 replicas of slow_encoder and 1 replica of fast_indexer
```

The above Flow will create a topology with three Replicas of Executor `slow_encoder`. The `Flow` will send every 
request to exactly one of the three instances. Then the replica will send its result to `fast_indexer`.


## Replicate on multiple GPUs

In certain situations, you may want to replicate your {class}`~jina.Executor`s so that each replica uses a different GPU on your machine.
To achieve this, you need to tell the {class}`~jina.Flow` to leverage multiple GPUs, by passing `CUDA_VISIBLE_DEVICES=RR` as an environment variable.
The Flow will then assign each available GPU to replicas in a round-robin fashion.

```{caution} 
Replicate on multiple GPUs by using `CUDA_VISIBLE_DEVICES=RR` should only be used locally.  
```

```{tip}
When working in Kubernetes or with Docker Compose you shoud allocate GPU ressources to each replica directly in the configuration files.
```

For example, if you have 3 GPUs and one of your Executor has 5 replicas then 

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

The Flow will assign GPU devices in the following round-robin fashion:

| GPU device | Replica ID |
|------------|------------|
| 0          | 0          |
| 1          | 1          |
| 2          | 2          |
| 0          | 3          |
| 1          | 4          |

 
You can also restrict the visible devices in round-robin assignment by `CUDA_VISIBLE_DEVICES=RR0:2`, where `0:2` has the same meaning as Python slice. This will create the following assignment:

| GPU device | Replica ID |
|------------|------------|
| 0          | 0          |
| 1          | 1          |
| 0          | 2          |
| 1          | 3          |
| 0          | 4          |


You can also restrict the visible devices in round-robin assignment by assigning a list of devices ids `CUDA_VISIBLE_DEVICES=RR1,3`. This will create the following assignment:

| GPU device | Replica ID |
|------------|------------|
| 1          | 0          |
| 3          | 1          |
| 1          | 2          |
| 3          | 3          |
| 1          | 4          |


## Distributed replicas

Replicas of the same Executor can run on different machines.

To add distributed replicas to a Flow, the Executor replicas must be running on their respective machines already.

````{admonition} External Executors
:class: seealso
For more information about starting Executors outside of a Flow, see our {ref}`how-to on external Executors <external-executor>`.
````

Then, you can add them by specifying their hosts, ports, and `external=True`:

```python
from jina import Flow

Flow().add(host='localhost:1234,91.198.174.192:12346', external=True)
```

This will connect to `grpc://localhost:12345` and `grpc://91.198.174.192:12346` as two replicas of the same Executor.


(partition-data-by-using-shards)=
## Partition data with shards

Sharding can be used to partition data (like an Index) into several parts. This enables the distribution of data across multiple machines.
This is helpful in two situations:

- When the full data does not fit on one machine 
- When the latency of a single request becomes too large.

Then splitting the load across two or more machines yields better results.

For Shards, you can define which shard (instance) will receive the request from its predecessor. This behaviour is called `polling`. `ANY` means only one shard will receive a request and `ALL` means that all Shards will receive a request.
Polling can be configured per endpoint (like `/index`) and {class}`~jina.Executor`.
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

The example above will result in a {class}`~jina.Flow` having the Executor `ExecutorWithShards` with the following polling options configured
- `/index` has polling `ANY` (the default value is not changed here)
- `/search` has polling `ANY` as it is explicitly set (usually that should not be necessary)
- `/custom` has polling `ALL`
- all other endpoints will have polling `ANY` due to the usage of `*` as a wildcard to catch all other cases


(flow-filter)=
## Filter by condition

To define a filter condition, you can use [DocArrays rich query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions).
You can set a filter for each individual {class}`~jina.Executor`, and every Document that does not satisfy the filter condition will be
removed before reaching that Executor.

To add a filter condition to an Executor, you pass it to the `when` parameter of {meth}`~jina.Flow.add` method of the Flow.
This then defines *when* a document will be processed by the Executor:

````{tab} Python

```{code-block} python
---
emphasize-lines: 4, 9
---

from jina import Flow, DocumentArray, Document

f = Flow().add().add(when={'tags__key': {'$eq': 5}})  # Create the empty Flow, add condition

with f:  # Using it as a Context Manager will start the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fullfilling the condition is processed and therefore returned.
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

with f:  # Using it as a Context Manager will start the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fullfilling the condition is processed and therefore returned.
```

```shell
[{'key': 5.0}]
```
````

Note that whenever a Document does not satisfy the `when` condition of a filter, the filter removes it *for the entire branch of the Flow*.
This means that every Executor that is located behind a filter is affected by this, not just the specific Executor that defines the condition.
Like with a real-life filter, once something does not pass through it, it will not re-appear behind the filter.

Naturally, parallel branches in a Flow do not affect each other. So if a Document gets filtered out in only one branch, it can
still be used in the other branch, and also after the branches are re-joined together:

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
It can also be used to build *switch-like nodes*, where some Documents pass through one parallel branch of the Flow,
while other Documents pass through a different branch.

Also note that whenever a Document does not satisfy the condition of an Executor, it will not even be sent to that Executor.
Instead, only a lightweight Request without any payload will be transferred.
This means that you can not only use this feature to build complex logic, but also to minimize your networking overhead.

````{admonition} See Also
:class: seealso

For a hands-on example on how to leverage these filter conditions, see {ref}`this how-to <flow-switch>`.
````
