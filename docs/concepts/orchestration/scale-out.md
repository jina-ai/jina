(scale-out)=
# Scale Out

By default, all Executors in an Orchestration run with a single instance. If an Executor is particularly slow, then it will reduce the overall throughput. To solve this, you can specify the number of `replicas` to scale out an Executor.

(replicate-executors)=
## Replicate stateless Executors

Replication creates multiple copies of the same {class}`~jina.Executor`. Each request in the Orchestration is then passed to only one replica (instance) of that Executor. **All replicas compete for a request. The idle replica gets the request first.**

This is useful for improving performance and availability:
* If you have slow Executors (e.g. embedding) you can scale up the number of instances to process multiple requests in parallel.
* Executors might need to be taken offline occasionally (for updates, failures, etc.), but you may want your Orchestration to still process requests without any downtime. Adding replicas allows any replica to be taken down as long as there is at least one still running. This ensures the high availability of your Orchestration.

### Replicate Executors in a Deployment

````{tab} Python
```python
from jina import Deployment

dep = Deployment(name='slow_encoder', replicas=3)
```
````
````{tab} YAML
```yaml
jtype: Deployment
uses: jinaai://jina-ai/CLIPEncoder
install_requirements: True
replicas: 5 
```
````

### Replicate Executors in a Flow

````{tab} Python
```python
from jina import Flow

f = Flow().add(name='slow_encoder', replicas=3).add(name='fast_indexer')
```
````
````{tab} YAML
```yaml
jtype: Flow
executors:
- uses: jinaai://jina-ai/CLIPEncoder
  install_requirements: True
  replicas: 5 
```
````

```{figure} images/replicas-flow.svg
:width: 70%
:align: center
Flow with three replicas of `slow_encoder` and one replica of `fast_indexer`
```

(scale-consensus)=
## Replicate stateful Executors with consensus using RAFT (Beta)

````{admonition} docarray 0.30
:class: note

Since docarray version > 0.30, docarray changed its interface and implementation drastically. We intend to support these new docarray versions
in the near future, but not every feature is yet available {ref}`Check here <docarray-v2>`. This feature has been added with these new docarray versions support.

This feature is only available when using `grpc` as the protocol for the Deployment or when the Deployment is part of a Flow
````

````{admonition} gRPC protocol
:class: note

This feature is only available when using gRPC as the protocol for the Deployment or when the Deployment is part of a Flow
````

Replication is used to scale-out Executors by creating copies of them that can handle requests in parallel providing better RPS.
However, when an Executor keeps some sort of state, then it is not simple to guarantee that each copy of the Executor keeps the same state,
which can lead to undesired behavior, since each replica can provide different results, depending on the specific state they hold.

In Jina, you can also have replication while guaranteeing the consensus between Executors. For this, we rely on (RAFT)[https://raft.github.io/] which is
an algorithm that guarantees eventual consistency between replicas. 

Consensus-based replication using RAFT is a distributed algorithm designed to provide fault tolerance and consistency in a distributed system. In a distributed system, the nodes may fail, and messages may be lost or delayed, which can lead to inconsistencies in the system.
The problem with traditional replication methods is that they can't guarantee consistency in a distributed system in the presence of failures. This is where consensus-based replication using RAFT comes in.
In this approach, each Executor can be considered as a Finite State Machine, which means that it has a set of states that it can be in, and a set of transitions that it can make between those states. Each request that is sent to the Executor can be considered as a log entry that needs to be replicated across the cluster.

In order to enable this kind of replication, we need to consider:

- Specify which methods of the Executor {ref}` could be updating its internal state <stateful-executor>`.
- Tell the deployment to use the RAFT consensus algorithm by setting the `--stateful` argument.
- Set values of replicas compatible with RAFT. RAFT requires a minimum of 3 replicas to guarantee consistency. 
- Pass the `--peer-ports` argument so that the RAFT cluster can recover from a previous configuration of replicas if existed.
- Optionally you can pass `--raft-configuration` parameter to tweak the behavior of the consensus module. You can understand the values to pass from
[Hashicorp's RAFT library](https://github.com/ongardie/hashicorp-raft/blob/master/config.go).

```python
from jina import Deployment, Executor, requests
from jina.serve.executors.decorators import write
from docarray import DocList
from docarray.documents import TextDoc


class MyStateStatefulExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs_dict = {}

    @requests(on=['/index'])
    @write
    def index(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            self._docs_dict[doc.id] = doc

    @requests(on=['/search'])
    def search(self,  docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            self.logger.debug(f'Searching against {len(self._docs_dict)} documents')
            doc.text = self._docs_dict[doc.id].text



d = Deployment(name='stateful_executor', 
               uses=MyStateStatefulExecutor,
               replicas=3, 
               stateful=True, 
               peer_ports=[12345, 12346, 12347])
with d:
    d.block()
```

This capacity allows us not only to have replicas work with robustness and availability, it also can help us to achieve higher throughput in some cases.

Let's imagine we write an Executor that is used to index and query documents from a vector index.

For this, we are going to use an in memory solution from [DocArray](https://docs.docarray.org/user_guide/storing/index_in_memory/) that performs exact vector search.

```python
from jina import Deployment, Executor, requests
from jina.serve.executors.decorators import write
from docarray import DocList
from docarray.documents import TextDoc
from docarray.index.backends.in_memory import InMemoryExactNNIndex


class QueryDoc(TextDoc):
    matches: DocList[TextDoc] = DocList[TextDoc]()


class ExactNNSearch(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._index = InMemoryExactNNIndex[TextDoc]()

    @requests(on=['/index'])
    @write # I add write decorator to indicate that calling this endpoint updates the inner state
    def index(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        self.logger.info(f'Indexing Document in index with {len(self._index)} documents indexed')
        self._index.index(docs)

    @requests(on=['/search'])
    def search(self,  docs: DocList[QueryDoc], **kwargs) -> DocList[QueryDoc]:
        self.logger.info(f'Searching Document in index with {len(self._index)} documents indexed')
        for query in docs:
            docs, scores = self._index.find(query, search_field='embedding', limit=10)
            query.matches = docs

d = Deployment(name='indexer',
               port=5555,
               uses=ExactNNSearch,
               workspace='./raft',
               replicas=3,
               stateful=True,
               peer_ports=[12345, 12346, 12347])
with d:
    d.block()
```

Then in another terminal, we are going to send index and search requests:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc
import time
import numpy as np

class QueryDoc(TextDoc):
    matches: DocList[TextDoc] = DocList[TextDoc]()

NUM_DOCS_TO_INDEX = 10000
NUM_QUERIES = 100

c = Client(port=5555)

index_docs = DocList[TextDoc]([TextDoc(text=f'I am document {i}', embedding=np.random.rand(128)) for i in range(NUM_DOCS_TO_INDEX)])
start_indexing_time = time.time()
c.post(on='/index', inputs=index_docs, request_size=100)
time.sleep(2) # let some time for the data to be replicated

search_da = DocList[QueryDoc]([QueryDoc(text=f'I am document {i}', embedding=np.random.rand(128)) for i in range(NUM_QUERIES)])
start_querying_time = time.time()
for query in search_da:
   responses = c.post(on='/search', inputs=query, request_size=1)
   for res in responses:
        print(f'{res.matches}')
```

In the logs of the `server` you can see how `index` requests reach every replica while `search` requests only reach one replica in a 
`round robin` fashion.

Eventually every Indexer replica ends up with the same Documents indexed. 

```text
INFO   indexer/rep-2@923 Indexing Document in index with 99900 documents indexed                                                                                                                                   
INFO   indexer/rep-0@902 Indexing Document in index with 99200 documents indexed                                                                                                                                   
INFO   indexer/rep-1@910 Indexing Document in index with 99700 documents indexed                                                                                                                                   
INFO   indexer/rep-1@910 Indexing Document in index with 99800 documents indexed                                                                                                                [04/28/23 16:51:06]
INFO   indexer/rep-0@902 Indexing Document in index with 99300 documents indexed                                                                                                                [04/28/23 16:51:06]
INFO   indexer/rep-1@910 Indexing Document in index with 99900 documents indexed                                                                                                                                   
INFO   indexer/rep-0@902 Indexing Document in index with 99400 documents indexed                                                                                                                                   
INFO   indexer/rep-0@902 Indexing Document in index with 99500 documents indexed                                                                                                                                   
INFO   indexer/rep-0@902 Indexing Document in index with 99600 documents indexed                                                                                                                                   
INFO   indexer/rep-0@902 Indexing Document in index with 99700 documents indexed                                                                                                                                   
INFO   indexer/rep-0@902 Indexing Document in index with 99800 documents indexed                                                                                                                                   
INFO   indexer/rep-0@902 Indexing Document in index with 99900 documents indexed 
```

But at search time, the consensus module does not affect, and only one replica serves the queries.
```text
INFO   indexer/rep-0@902 Searching Document in index with 100000 documents indexed                                                                                                              [04/28/23 16:59:21]
INFO   indexer/rep-1@910 Searching Document in index with 100000 documents indexed                                                                                                              [04/28/23 16:59:21]
INFO   indexer/rep-2@923 Searching Document in index with 100000 documents indexed 
```

## Replicate on multiple GPUs

To replicate your {class}`~jina.Executor`s so that each replica uses a different GPU on your machine, you can tell the Orchestration to use multiple GPUs by passing `CUDA_VISIBLE_DEVICES=RR` as an environment variable.

```{caution} 
You should only replicate on multiple GPUs with `CUDA_VISIBLE_DEVICES=RR` locally.  
```

```{tip}
In Kubernetes or with Docker Compose you should allocate GPU resources to each replica directly in the configuration files.
```

The Orchestration assigns GPU devices in the following round-robin fashion:

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

You can also refer to GPUs by their UUID. For instance, you could assign a list of device UUIDs:

```bash
CUDA_VISIBLE_DEVICES=RRGPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5,GPU-0bbbbbbb-74d2-7297-d557-12771b6a79d5,GPU-0ccccccc-74d2-7297-d557-12771b6a79d5,GPU-0ddddddd-74d2-7297-d557-12771b6a79d5
```

Check [CUDA Documentation](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#env-vars) to see the accepted formats to assign CUDA devices by UUID.

| GPU device | Replica ID |
|------------|------------|
| GPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5          | 0          |
| GPU-0bbbbbbb-74d2-7297-d557-12771b6a79d5          | 1          |
| GPU-0ccccccc-74d2-7297-d557-12771b6a79d5          | 2          |
| GPU-0ddddddd-74d2-7297-d557-12771b6a79d5          | 3          |
| GPU-0aaaaaaa-74d2-7297-d557-12771b6a79d5          | 4          |


For example, if you have three GPUs and one of your Executor has five replicas then:

### GPU replicas in a Deployment

````{tab} Python
```python
from jina import Deployment

dep = Deployment(uses='jinaai://jina-ai/CLIPEncoder', replicas=5, install_requirements=True)

with dep
    dep.block()
```

```shell
CUDA_VISIBLE_DEVICES=RR python deployment.py
```
````

````{tab} YAML
```yaml
jtype: Deployment
with:
  uses: jinaai://jina-ai/CLIPEncoder
  install_requirements: True
  replicas: 5  
```

```shell
CUDA_VISIBLE_DEVICES=RR jina deployment --uses deployment.yaml
```
````

### GPU replicas in a Flow

````{tab} Python
```python
f = Flow().add(
    uses='jinaai://jina-ai/CLIPEncoder', replicas=5, install_requirements=True
) 

with f:
    f.block()
```

```shell
CUDA_VISIBLE_DEVICES=RR python flow.py
```
````

````{tab} YAML
```yaml
jtype: Flow
executors:
- uses: jinaai://jina-ai/CLIPEncoder
  install_requirements: True
  replicas: 5  
```

```shell
CUDA_VISIBLE_DEVICES=RR jina flow --uses flow.yaml
```
````

## Replicate external Executors

If you have external Executors with multiple replicas running elsewhere, you can add them to your Orchestration by specifying all the respective hosts and ports:

````{tab} Deployment
```python
from jina import Deployment

replica_hosts, replica_ports = ['localhost','91.198.174.192'], ['12345','12346']
Deployment(host=replica_hosts, port=replica_ports, external=True)

# alternative syntax
Deployment(host=['localhost:12345','91.198.174.192:12346'], external=True)
```
````
````{tab} Flow
```python
from jina import Flow

replica_hosts, replica_ports = ['localhost','91.198.174.192'], ['12345','12346']
Flow().add(host=replica_hosts, port=replica_ports, external=True)

# alternative syntax
Flow().add(host=['localhost:12345','91.198.174.192:12346'], external=True)
```
````

This connects to `grpc://localhost:12345` and `grpc://91.198.174.192:12346` as two replicas of the external Executor.

````{admonition} Reducing
:class: hint
If an external Executor needs multiple predecessors, reducing needs to be enabled. So setting `no_reduce=True` is not allowed for these cases. 
````

(partition-data-by-using-shards)=
## Customize polling behaviors

Replicas compete for a request, so only one of them will get the request. What if we want all replicas to get the request? 

For example, consider index and search requests:

- Index (and update, delete) are handled by a single replica, as this is sufficient to add it one time.
- Search requests are handled by all replicas, as you need to search over all replicas to ensure the completeness of the result. The requested data could be on any shard.

For this purpose, you need `shards` and `polling`.

You can define if all or any `shards` receive the request by specifying `polling`. `ANY` means only one shard receives the request, while  `ALL` means that all shards receive the same request.

````{tab} Deployment
```python
from jina import Deployment

dep = Deployment(name='ExecutorWithShards', shards=3, polling={'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'})
```
````
````{tab} Flow
```python
from jina import Flow

f = Flow().add(name='ExecutorWithShards', shards=3, polling={'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'})
```
````

The above example results in an Orchestration having the Executor `ExecutorWithShards` with the following polling options:
- `/index` has polling `ANY` (the default value is not changed here).
- `/search` has polling `ANY` as it is explicitly set (usually that should not be necessary).
- `/custom` has polling `ALL`.
- All other endpoints have polling `ANY` due to using `*` as a wildcard to catch all other cases.

### Understand behaviors of replicas and shards with polling

The following example demonstrates the different behaviors when setting `replicas`, `shards` and `polling` together.

````{tab} Deployment
```{code-block} python
---
emphasize-lines: 12
---
from jina import Deployment, Document, Executor, requests


class MyExec(Executor):

    @requests
    def foo(self, docs, **kwargs):
        print(f'inside: {docs.texts}')


dep = (
    Deployment(uses=MyExec, replicas=2, polling='ANY')
    .needs_all()
)

with dep:
    r = dep.post('/', Document(text='hello'))
    print(f'return: {r.texts}')
```
````
````{tab} Flow
```{code-block} python
---
emphasize-lines: 13
---
from jina import Flow, Document, Executor, requests


class MyExec(Executor):

    @requests
    def foo(self, docs, **kwargs):
        print(f'inside: {docs.texts}')


f = (
    Flow()
    .add(uses=MyExec, replicas=2, polling='ANY')
    .needs_all()
)

with f:
    r = f.post('/', Document(text='hello'))
    print(f'return: {r.texts}')
```
````

We now change the combination of the yellow highlighted lines above and see if there is any difference in the console output (note two prints in the snippet):

|               	 |  `polling='ALL'`                                        	 |  `polling='ANY'`                     	 |
| --------------   |  --------------------------------------------------------  | -------------------------------------  |
| `replicas=2`     |           `inside: ['hello'] return: ['hello']`            | `inside: ['hello'] return: ['hello']`  |
| `shards=2`       |  `inside: ['hello'] inside: ['hello']  return: ['hello']`  | `inside: ['hello'] return: ['hello']`  |
