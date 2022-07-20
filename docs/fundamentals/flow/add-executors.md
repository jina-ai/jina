(flow-add-executors)=
# Add Executors

A {class}`~jina.Flow` orchestrates its {class}`~jina.Executor`s as a graph and will send requests to all Executors in the desired order. Executors can be added with the {meth}`~jina.Flow.add` method of the Flow or be listed in the yaml configuration of a Flow. When you start a Flow, it will check the configured Executors and starts instances of these Executors accordingly. When adding Executors you have to define its type with the `uses` keyword. Executors can be used from various sources like code, docker images and the Hub:

````{tab} Python

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


f = (
    Flow()
    .add(uses=FooExecutor, name='fooExecutor')
    .add(uses=BarExecutor, name='barExecutor')
)  # Create the empty Flow
with f:  # Using it as a Context Manager will start the Flow
    response = f.post(
        on='/search'
    )  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```
````

`````{tab} YAML
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

`main.py`
```python
from jina import Flow

f = Flow.load_config('flow.yml')

with f:
    response = f.post(
        on='/search'
    )  # This sends a request to the /search endpoint of the Flow
    print(response.texts)
```

````{admonition} Hint: Load multiple Executors from the same module
:class: hint

You can override the `metas` attribute for all Executors in a Flow. This allows you to specify a single Python module
from which you can then load all of your Executors, without having to specify the module individually for each Executor:

```yaml
jtype: Flow
metas:
  py_modules:
    - executors.py
executors:
  - uses: FooExecutor
  - uses: BarExecutor
```

In this example, both `FooExecutor` and `BarExecutor` are defined inside of `executors.py`, and both will be located and loaded by the Flow.
````
`````


The response of the Flow defined above is `['foo was here', 'bar was here']`, because the request was first sent to FooExecutor and then to BarExecutor.

## Supported Executors

As explained above, the type of {class}`~jina.Executor` is defined by providing the `uses` keyword. The source of an Executor can be code, docker images or Hub images.

```python
class ExecutorClass(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))


f = (
    Flow()
    .add(uses=ExecutorClass, name='executor1')
    .add(uses='jinahub://TransformerTorchEncoder/', name='executor2')
    .add(uses='jinahub+docker://TransformerTorchEncoder', name='executor3')
    .add(uses='jinahub+sandbox://TransformerTorchEncoder', name='executor4')
    .add(uses='docker://sentence-encoder', name='executor5')
    .add(uses='executor-config.yml', name='executor6')
)
```

* `executor1` will use `ExecutorClass` from code, and will be created as a separate process.
* `executor2` will download the Executor class from Hub, and will be created as a separate process.
* `executor3` will use an Executor docker image coming from the Hub, and will be created as a docker container of this image.
* `executor4` will use a {ref}`Sandbox Executor <sandbox>` run by Hubble, in the cloud.
* `executor5` will use a Docker image tagged as `sentence-encoder`, and will be created as a docker container of this image.
* `executor6` will use an Executor configuration file defining the {ref}`Executor YAML interface <executor-api>`, and will be created as a separate process.

More complex Executors typically are used from Docker images or will be structured into separate Python modules. 


````{admonition} Hint: Load multiple Executors from the same directory
:class: hint

If you want to load multiple Executor YAMLs from the same directory, you don't need to specify the parent directory for
each Executor.
Instead, you can configure a common search path for all Executors:

```
.
├── app
│   └── ▶ main.py
└── executor
    ├── config1.yml
    ├── config2.yml
    └── my_executor.py
```

```{code-block} python
f = Flow(extra_search_paths=['../executor']).add(uses='config1.yml').add(uses='config2.yml')
```

````
(external-executors)=
### External Executors

Usually a Flow will manage all of its Executors. External Executors are not managed by the current Flow object but by others. For example, one may want to share expensive Executors between Flows. Often these Executors are stateless, GPU based Encoders.

Those Executors are marked with the `external` keyword when added to a `Flow`:

```python
from jina import Flow

Flow().add(host='123.45.67.89', port=12345, external=True)
```

This is adding an external Executor to the Flow. The Flow will not start or stop this Executor and assumes that is externally managed and available at `123.45.67.89:12345`

You can also use external Executors with `tls` enabled.

```python
from jina import Flow

Flow().add(host='123.45.67.89', port=443, external=True, tls=True)
```

```{hint} 
Using `tls` to connect to the External Executor is especially needed if you want to use an external Executor deployed with JCloud. See the JCloud {ref}`documentation <jcloud-external-executors>`
for further details
```


(floating-executors)=
### Floating Executors

Some Executors in your Flow may be used for asynchronous background tasks that can take some time and that do not generate a needed output. For instance,
logging specific information in external services, storing partial results, etc.

You can unblock your Flow from such tasks by using *floating Executors*.

Normally, all Executors form a pipeline that handles and transforms a given request until it is finally returned to the Client.

However, floating Executors do not feed their outputs back to the pipeline. Therefore, this output will not form the response for the Client, and the response can be returned without waiting for the floating Executor to complete his task.
 
Those Executors are marked with the `floating` keyword when added to a `Flow`:

```python
import time
from jina import Flow, Executor, requests, DocumentArray


class FastChangingExecutor(Executor):
    @requests()
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Hello World'


class SlowChangingExecutor(Executor):
    @requests()
    def foo(self, docs, **kwargs):
        time.sleep(2)
        print(f' Received {docs.texts}')
        for doc in docs:
            doc.text = 'Change the document but will not affect response'


f = (
    Flow()
    .add(name='executor0', uses=FastChangingExecutor)
    .add(
        name='floating_executor',
        uses=SlowChangingExecutor,
        needs=['gateway'],
        floating=True,
    )
)
with f:
    f.post(on='/endpoint', inputs=DocumentArray.empty(1))  # we need to send a first
    start_time = time.time()
    response = f.post(on='/endpoint', inputs=DocumentArray.empty(2))
    end_time = time.time()
    print(f' Response time took {end_time - start_time}s')
    print(f' {response.texts}')
```

```text
 Response time took 0.011997222900390625s
 ['Hello World', 'Hello World']
 Received ['Hello World', 'Hello World']
```

In this example you can see how the response is returned without waiting for the `floating` Executor to complete. However, the Flow is not closed until
the request has been handled also by it.


You can plot the Flow and observe how the Executor is floating disconnected from the **Gateway**.

```{figure} flow_floating.svg
:width: 70%

```
A floating Executor can never come before a non-floating Executor in the {ref}`topology <flow-complex-topologies>` of your Flow.

This leads to the following behaviors:

- **Implicit reordering**: When adding a non-floating Executor after a floating Executor without specifying its `needs` parameter, the non-floating Executor is chained after the previous non-floating one.
```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add()
f.plot()
```

```{figure} flow_middle_1.svg
:width: 70%

```

- **Chaining floating Executors**: If you want to chain more than one floating Executor, you need to add all of them with the `floating` flag, and explicitly specify the `needs` argument.

```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add(needs=['middle'], floating=True)
f.plot()
```

```{figure} flow_chain_floating.svg
:width: 70%

```

- **Overriding of `floating` flag**: If you try to add a floating Executor as part of `needs` parameter of a non-floating Executor, then the floating Executor is not considered floating anymore.

```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add(needs=['middle'])
f.plot()
```

```{figure} flow_cancel_floating.svg
:width: 70%

```


## Set configs
You can set and override {class}`~jina.Executor` configs when adding them into a {class}`~jina.Flow`.

This example shows how to start a Flow with an Executor via the Python API:

```python
from jina import Flow

with Flow().add(
    uses='MyExecutor',
    uses_with={"parameter_1": "foo", "parameter_2": "bar"},
    uses_metas={
        "name": "MyExecutor",
        "description": "MyExecutor does a thing to the stuff in your Documents",
        "py_modules": ["executor.py"],
    },
    uses_requests={"/index": "my_index", "/search": "my_search", "/random": "foo"},
    workspace="some_custom_path",
) as f:
    ...
```

- `uses_with` is a key-value map that defines the {ref}`arguments of the Executor'<executor-args>` `__init__` method.
- `uses_metas` is a key-value map that defines some {ref}`internal attributes<executor-metas>` of the Executor. It contains the following fields:
    - `name` is a string that defines the name of the executor;
    - `description` is a string that defines the description of this executor. It will be used in automatic docs UI;
    - `py_modules` is a list of strings that defines the Python dependencies of the executor;
- `uses_requests` is a key-value map that defines the {ref}`mapping from endpoint to class method<executor-requests>`. Useful if one needs to overwrite the default endpoint-to-method mapping defined in the Executor python implementation.
- `workspace` is a string value that defines the {ref}`workspace <executor-workspace>`.


### Set `metas` via `uses_metas`

To set/override the `metas` configuration of an executor, use `uses_metas`:

```python
from jina import Executor, requests, Flow


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print(self.metas.name)


flow = Flow().add(
    uses=MyExecutor,
    uses_metas={'name': 'different_name'},
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
different_name
```


### Set `with` via `uses_with`

To set/override the `with` configs of an executor, use `uses_with`. The `with` configuration refers to user-defined 
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

### Set `requests` via `uses_requests`
You can set/override the `requests` configuration of an executor and bind methods to endpoints that you provide. 
In the following codes, we replace the endpoint `/foo` binded to the `foo()` function with both `/non_foo` and `/alias_foo`. 
And add a new endpoint `/bar` for binding `bar()`. Note the `all_req()` function is binded to **all** the endpoints except those explicitly bound to other functions, i.e. `/non_foo`, `/alias_foo` and `/bar`.

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


flow = Flow().add(
    uses=MyExecutor,
    uses_requests={
        '/bar': 'bar',
        '/non_foo': 'foo',
        '/alias_foo': 'foo',
    },
)
with flow as f:
    f.post('/bar', parameters={'recipient': 'bar()'})
    f.post('/non_foo', parameters={'recipient': 'foo()'})
    f.post('/foo', parameters={'recipient': 'all_req()'})
    f.post('/alias_foo', parameters={'recipient': 'foo()'})
```

```text
      executor0@221058[L]:ready and listening
        gateway@221058[L]:ready and listening
           Flow@221058[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:36507
	🔒 Private network:	192.168.1.101:36507
	🌐 Public address:	197.28.82.165:36507
bar bar()
foo foo()
all req all_req()
foo foo()
```

## Unify NDArray types

Different {class}`~jina.Executor`s in a {class}`~jina.Flow` may depend on slightly different `types` for array-like data such as `doc.tensor` and `doc.embedding`,
for example because they were written using different machine learning frameworks.
As the builder of a Flow you don't always have control over this, for example when using Executors from the Jina Hub.

In order to facilitate the integration between different Executors, the Flow allows you to convert `tensor` and `embedding`
by using the `f.add(..., output_array_type=..)`:

```python
from jina import Flow

f = Flow().add(uses=MyExecutor, output_array_type='numpy').add(uses=NeedsNumpyExecutor)
```

This converts the `.tensor` and `.embedding` fields of all output Documents of `MyExecutor` to `numpy.ndarray`, making the data
usable by `NeedsNumpyExecutor`. This works regardless of whether MyExecutor populates these fields with arrays/tensors from
PyTorch, TensorFlow, or any other popular ML framework.

````{admonition} Output types
:class: note

`output_array_type=` supports more types than `'numpy'`. For a full specification, and further details, take a look at the
documentation about [protobuf serialization](https://docarray.jina.ai/fundamentals/document/serialization/#from-to-protobuf).
````

