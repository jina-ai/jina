Open questions:
Does polling/sharding/replicas belong here?

# Create a Flow

A `Flow` can by created as a Python object and can be easily used as a Context Manager. The Context Manager will make sure that the `Flow` will be started and closed correctly. Starting a `Flow` means starting of all its Executors.

The most trivial `Flow` is the empty `Flow` as shown below:

````{tab} Pythonic style

```python
from jina import Flow

f = Flow() # Create the empty Flow
with f: # Using it as a Context Manager will start the Flow
    f.search() # This sends a request to the /search endpoint of the Flow
```
````

````{tab} Load from YAML
`flow.yml`:

```yaml
jtype: Flow
```

```python
from jina import Flow, Document

f = Flow.load_config('flow.yml') # Load the Flow definition from Yaml file

with f: # Using it as a Context Manager will start the Flow
    f.search() # This sends a request to the /search endpoint of the Flow
```
````

## Add Executors
Content:
* explain sources of executors (docker, jinahub, local)

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
    response = f.search(return_results=True)  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```
````

````{tab} Load from YAML
TODO do yaml example
```
````
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/foobar_flow.png?raw=true" alt="Simple Flow with two Executors being chained one after the other" width="50%">


The response of `Flow` defined above is `['foo was here', 'bar was here']`, because the request was first sent to FooExecutor and then to BarExecutor.

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
from jina import Executor, DocumentArray, requests

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
emphasize-lines: 2
---
from jina import Flow, Document
f = Flow(extra_search_paths=['../executor']).add(uses='config.yml')
with f:
    r = f.post('/', inputs=Document())
```
````

````{tab} Load from YAML
```
`flow.yml`:
```yaml
jtype: Flow
executors:
  - name: executor
    uses: ../executor/config.yml
```

`main.py`:
```python
from jina import Flow, Document
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

### Pre- and Post-processing

explain uses_before/uses_after?

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
A typical use case for such a Flow is a topology with a common pre-processing part, but indexers separating embeddings and data.
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
    response = f.search(return_results=True)  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/foobarbaz_flow_needs.png?raw=true" alt="Simple Flow with two Executors being chained one after the other" width="50%">
This will get you the following output:
```text
['foo was here and got 0 document', 'bar was here and got 1 document', 'baz was here and got 1 document']
```
So both `BarExecutor` and `BazExecutor` received only received a single `Document` from `FooExecutor` as they are run in parallel. The last Executor `executor3` will receive both DocumentArrays and merges them automatically.

## Visualize a `Flow`

`Flow` has a built-in `.plot()` function which can be used to visualize a `Flow`:
```python
from jina import Flow

f = Flow().add().add()
f.plot()
```

This will output mermaid link visualizing the `Flow`.