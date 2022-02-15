(flow)=
# Create a Flow

A `Flow` can be created as a Python object and can be easily used as a Context Manager. The Context Manager will make sure that the `Flow` will be started and closed correctly. Starting a `Flow` means starting all its Executors.

The most trivial `Flow` is the empty `Flow` as shown below:

````{tab} Pythonic style

```python
from jina import Flow

f = Flow() # Create the empty Flow
with f: # Using it as a Context Manager will start the Flow
    f.post(on='/search') # This sends a request to the /search endpoint of the Flow
```
````

````{tab} Load from YAML
`flow.yml`:

```yaml
jtype: Flow
```

```python
from jina import Flow

f = Flow.load_config('flow.yml') # Load the Flow definition from Yaml file

with f: # Using it as a Context Manager will start the Flow
    f.post(on='/search') # This sends a request to the /search endpoint of the Flow
```
````

## Visualize a `Flow`

`Flow` has a built-in `.plot()` function which can be used to visualize a `Flow`:
```python
from jina import Flow

f = Flow().add().add()
f.plot('flow.svg')
```

```{figure} flow.svg
:width: 70%
The generated SVG file visualizing the `Flow` above.
```


## Add Executors
A `Flow` orchestrates its Executors as a graph and will send requests to all Executors in the desired order. Executors can be added with the `.add()` method of the `Flow` or be listed in the yaml configuration of a Flow. When you start a `Flow`, it will check the configured Executors and starts instances of these Executors accordingly. When adding Executors you have to define its type with the `uses` keyword. Executors can be used from various sources like code, docker images and the Hub:

````{tab} Pythonic style

```python
from docarray import Document, DocumentArray
from jina import Executor, Flow, requests

class FooExecutor(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))

class BarExecutor(Executor):

    @requests
    def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='bar was here'))

f = Flow().add(uses=FooExecutor, name='fooExecutor').add(uses=BarExecutor, name='barExecutor')  # Create the empty Flow
with f:  # Using it as a Context Manager will start the Flow
    response = f.post(on='/search', return_results=True)  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```
````

````{tab} Load from YAML
`flow.yml`:

```yaml
jtype: Flow
executors:
  - name: myexec1
    uses: FooExecutor
    py_modules: exec.py
  - name: myexec2
    uses: BarExecutor
    py_modules: exec.py
```

`exec.py`
```python
from docarray import Document, DocumentArray

from jina import Executor, requests


class FooExecutor(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))


class BarExecutor(Executor):

    @requests
    def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='bar was here'))
```

```python
from jina import Flow

f = Flow.load_config('flow.yml')

with f:
    response = f.post(on='/search', return_results=True)  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```
```
````


The response of the `Flow` defined above is `['foo was here', 'bar was here']`, because the request was first sent to FooExecutor and then to BarExecutor.

### Executor discovery
As explained above, the type of Executor is defined by providing the `uses` keyword. The source of an Executor can be code, docker images or Hub images.

```python
class ExecutorFromCode(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))

f = Flow()\
    .add(uses='docker://sentence-encoder', name='executor1')\
    .add(uses='jinahub+docker://TransformerTorchEncoder/', name='executor2')\
    .add(uses=ExecutorFromCode, name='executor3')

```
* `executor1` is using a Docker image tagged as `sentence-encoder` and will be created as a docker container of this image. 
* `executor2` will use a Docker image coming from the Hub and will be created as a docker container of this image.
* `executor3` will be used from code and will be created as a separate process.

More complex Executors typically are used from Docker images or will be structured into separate Python modules. 

You can use Executors from code, being defined outside your current `PATH` environment variable. To do this you need to define your Executor configuration in a separate configuration yaml, which will be used in the `Flow`:

```
.
├── app
│   └── ▶ main.py
└── executor
    ├── config.yml
    └── my_executor.py
```
`executor/my_executor.py`:
```python
from docarray import DocumentArray
from jina import Executor, requests

class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        pass
```

`executor/config.yml`:
```yaml
jtype: MyExecutor
metas:
  py_modules:
    - executor.py
```

Now, in `app/main.py`, to correctly load the Executor, you can specify the directory of the Executor in Python or in a `Flow` yaml:
````{tab} Load from YAML
```{code-block} python
---
emphasize-lines: 3
---
from docarray import Document
from jina import Flow
f = Flow(extra_search_paths=['../executor']).add(uses='config.yml')
with f:
    r = f.post('/', inputs=Document())
```
````

````{tab} Load from YAML
`flow.yml`:
```yaml
jtype: Flow
executors:
  - name: executor
    uses: ../executor/config.yml
```

`main.py`:
```python
from docarray import Document
from jina import Flow
f = Flow.load_config('../flow/flow.yml')
with f:
    r = f.post('/', inputs=Document())
```
````

### Override Executor configuration
You can override the various configuration options available to Executors when adding them into a `Flow`.

#### Override `metas` configuration
To override the `metas` configuration of an executor, use `uses_metas`:
```python
from jina import Executor, requests, Flow
class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print(self.metas.workspace)

flow = Flow().add(
    uses=MyExecutor,
    uses_metas={'workspace': 'different_workspace'},
)
with flow as f:
    f.post('/')
```

```text
      executor0@219291[L]:ready and listening
        gateway@219291[L]:ready and listening
           Flow@219291[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:58827
	🔒 Private network:	192.168.1.101:58827
different_workspace
```


#### Override `with` configuration
To override the `with` configuration of an executor, use `uses_with`. The `with` configuration refers to user-defined 
constructor kwargs.
```python
from jina import Executor, requests, Flow

class MyExecutor(Executor):
    def __init__(self, param1=1, param2=2, param3=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3

    @requests
    def foo(self, docs, **kwargs):
        print('param1:', self.param1)
        print('param2:', self.param2)
        print('param3:', self.param3)

flow = Flow().add(uses=MyExecutor, uses_with={'param1': 10, 'param3': 30})
with flow as f:
    f.post('/')
```
```text
      executor0@219662[L]:ready and listening
        gateway@219662[L]:ready and listening
           Flow@219662[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:32825
	🔒 Private network:	192.168.1.101:32825
	🌐 Public address:	197.28.82.165:32825
param1: 10
param2: 2
param3: 30
```

#### Override `requests` configuration
You can override the `requests` configuration of an executor and bind methods to endpoints that you provide. In the following codes, we replace the endpoint `/foo` binded to the `foo()` function with `/non_foo` and add a new endpoint `/bar` for binding `bar()`. Note the `all_req()` function is binded to **all** the endpoints except those explicitly binded to other functions, i.e. `/non_foo` and `/bar`.

```python
from jina import Executor, requests, Flow

class MyExecutor(Executor):
    @requests
    def all_req(self, parameters, **kwargs):
        print(f'all req {parameters.get("recipient")}')
        
    @requests(on='/foo')
    def foo(self, parameters, **kwargs):
        print(f'foo {parameters.get("recipient")}')
    
    def bar(self, parameters, **kwargs):
        print(f'bar {parameters.get("recipient")}')

flow = Flow().add(uses=MyExecutor, uses_requests={'/bar': 'bar', '/non_foo': 'foo', })
with flow as f:
    f.post('/bar', parameters={'recipient': 'bar()'})
    f.post('/non_foo', parameters={'recipient': 'foo()'})
    f.post('/foo', parameters={'recipient': 'all_req()'})
```

```text
      executor0@221058[L]:ready and listening
        gateway@221058[L]:ready and listening
           Flow@221058[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:36507
	🔒 Private network:	192.168.1.101:36507
	🌐 Public address:	197.28.82.165:36507
bar
foo
```

### External executors
Usually a `Flow` will manage all of its Executors. 
In some cases it is desirable though to use externally managed Executors. These are named `external Executors`. This is especially useful to share expensive Executors between Flows. Often these Executors are stateless, GPU based Encoders.
Those Executors are marked with the `external` keyword when added to a `Flow`:
```python
from jina import Flow
Flow().add(host='123.45.67.89', port_in=12345, external=True)
```
This is adding an external Executor to the Flow. The Flow will not start or stop this Executor and assumes that is externally managed and available at `123.45.67.89:12345`


## Complex Flow topologies
Flows are not restricted to sequential execution. Internally they are modelled as graphs and as such can represent any complex, non-cyclic topology.
A typical use case for such a Flow is a topology with a common pre-processing part, but different indexers separating embeddings and data.
To define a custom `Flow` topology you can use the `needs` keyword when adding an Executor. By default, a `Flow` assumes that every Executor needs the previously added Executor.

```python
from docarray import Document, DocumentArray
from jina import Executor, Flow, requests


class FooExecutor(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'foo was here and got {len(docs)} document'))


class BarExecutor(Executor):

    @requests
    def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'bar was here and got {len(docs)} document'))


class BazExecutor(Executor):

    @requests
    def baz(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'baz was here and got {len(docs)} document'))


f = Flow() \
    .add(uses=FooExecutor, name='fooExecutor') \
    .add(uses=BarExecutor, name='barExecutor', needs='fooExecutor') \
    .add(uses=BazExecutor, name='bazExecutor', needs='fooExecutor') \
    .add(needs=['barExecutor', 'bazExecutor'])

with f:  # Using it as a Context Manager will start the Flow
    response = f.post(on='/search', return_results=True)  # This sends a request to the /search endpoint of the Flow
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

So both `BarExecutor` and `BazExecutor` received only received a single `Document` from `FooExecutor` as they are run in parallel. The last Executor `executor3` will receive both DocumentArrays and merges them automatically.

### Replicate Executors

Replication can be used to create multiple copies of the same Executor. Each request in the Flow is then passed to only one replica (instance) of your Executor. This can be useful for a couple of challenges like performance and availability:
* If you have slow Executors (like some Encoders) you may want to scale up the number of instances of this particular Executor so that you can process multiple requests in parallel
* Executors might need to be taken offline from time to time (updates, failures, etc.), but you may want your Flow to be able to process requests without downtimes. In this case Replicas can be used as well so that any Replica of an Executor can be taken offline as long as there is still one running Replica online. Using this technique it is possible to create a High availability setup for your Flow.

```python
from jina import Flow

f = (Flow()
     .add(name='slow_encoder', replicas=3)
     .add(name='fast_indexer'))
```

```{figure} replicas-flow.svg
:width: 70%
:align: center
Flow with 3 replicas of slow_encoder and 1 replica of fast_indexer
```

The above Flow will create a topology with three Replicas of Executor `slow_encoder`. The `Flow` will send every 
request to exactly one of the three instances. Then the replica will send its result to `fast_indexer`.

### Partition data by using Shards

Sharding can be used to partition data (like an Index) into several parts. This enables the distribution of data across multiple machines.
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



