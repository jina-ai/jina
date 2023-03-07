(flow-complex-topologies)=
# Scale Out

By default, all Executors in a {class}`~jina.Deployment` or {class}`~jina.Flow` run with a single instance. If an Executor is particularly slow, then it will reduce the overall throughput. To solve this, you can specify the number of `replicas` to scale out an Executor.

(replicate-executors)=
## Replicate Executors

Replication creates multiple copies of the same {class}`~jina.Executor`. Each request in the {class}`~jina.Orchestration` is then passed to only one replica (instance) of that Executor. **All replicas compete for a request. The idle replica gets the request first.**

This is useful for improving performance and availability:
* If you have slow Executors (e.g. embedding) you can scale up the number of instances to process multiple requests in parallel.
* Executors might need to be taken offline occasionally (for updates, failures, etc.), but you may want your Orchestration to still process requests without any downtime. Adding replicas allows any replica to be taken down as long as there is at least one still running. This ensures the high availability of your Orchestration.

````{tab} Deployment (Python)
```python
from jina import Deployment

dep = Deployment(name='slow_encoder', replicas=3)
```
````
````{tab} Deployment (YAML)
```python
from jina import Deployment

dep = Deployment(name='slow_encoder', replicas=3)
```
````
````{tab} Flow (Python)
```python
from jina import Flow

f = Flow().add(name='slow_encoder', replicas=3).add(name='fast_indexer')
```
````
````{tab} Flow (YAML)
```python
from jina import Flow

f = Flow().add(name='slow_encoder', replicas=3).add(name='fast_indexer')
```
````

```{figure} images/replicas-flow.svg
:width: 70%
:align: center
Flow with three replicas of `slow_encoder` and one replica of `fast_indexer`
```

## Replicate on multiple GPUs

To replicate your {class}`~jina.Executor`s so that each replica uses a different GPU on your machine, you can tell the Orchestration to use multiple GPUs by passing `CUDA_VISIBLE_DEVICES=RR` as an environment variable.
The Orchestration then assigns each available GPU to replicas in a round-robin fashion.

```{caution} 
You should only replicate on multiple GPUs with `CUDA_VISIBLE_DEVICES=RR` locally.  
```

```{tip}
In Kubernetes or with Docker Compose you should allocate GPU resources to each replica directly in the configuration files.
```

For example, if you have three GPUs and one of your Executor has five replicas then:

````{tab} Deployment (Python)
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

````{tab} Deployment (YAML)
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
````{tab} Flow (Python)
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

````{tab} Flow (YAML)
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
