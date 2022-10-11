(flow-add-executors)=
# Add Executors

A {class}`~jina.Flow` orchestrates its {class}`~jina.Executor`s as a graph and sends requests to all Executors in the order specified by {meth}`~jina.Flow.add` or listed in {ref}`a YAML file<flow-yaml-spec>`. 

When you start a Flow, Executors always run in **separate processes**. Multiple Executors run in **different processes**. Multiprocessing is the lowest level of separation when you run a Flow locally. When running a Flow on Kubernetes, Docker Swarm, {ref}`jcloud`, different Executors run in different containers, pods or instances.   

## Add Executors

Executors can be added into a Flow with {meth}`~jina.Flow.add`.  

```python
from jina import Flow

f = Flow().add()
```

This adds an "empty" Executor called {class}`~jina.Executor.BaseExecutor` to the Flow. This Executor (without any parameters) performs no actions.

```{figure} no-op-flow.svg
:scale: 70%
```

To more easily identify an Executor, you can change its name by passing the `name` parameter:

```python
from jina import Flow

f = Flow().add(name='myVeryFirstExecutor').add(name='secondIsBest')
```


```{figure} named-flow.svg
:scale: 70%
```

You can also define the above Flow in YAML:

```yaml
jtype: Flow
executors:
  - name: myVeryFirstExecutor
  - name: secondIsBest
```

Save it as `flow.yml` and run it: 

```bash
jina flow --uses flow.yml
```

More Flow YAML specifications can be found in {ref}`Flow YAML Specification<flow-yaml-spec>`.


## Define Executor types with `uses`

An {class}`~jina.Executor`'s type is defined by the `uses` keyword. Note that some usages are not supported on JCloud due to security reasons and the nature of facilitating local debugging.

| Local Dev | JCloud | `.add(uses=...)`                              | Description                                                                                               |
|-----------|--------|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| ✅         | ❌      | `ExecutorClass`                               | Use `ExecutorClass` from the inline context.                                                              |
| ✅         | ❌      | `'my.py_modules.ExecutorClass'`               | Use `ExecutorClass` from `my.py_modules`.                                                                 |
| ✅         | ✅      | `'executor-config.yml'`                       | Use an Executor from a YAML file defined by {ref}`Executor YAML interface <executor-yaml-spec>`.          |
| ✅         | ❌      | `'jinahub://TransformerTorchEncoder/'`        | Use an Executor as Python source from Jina Hub.                                                           |
| ✅         | ✅      | `'jinahub+docker://TransformerTorchEncoder'`  | Use an Executor as a Docker container from Jina Hub.                                                      |
| ✅         | ✅      | `'jinahub+sandbox://TransformerTorchEncoder'` | Use a {ref}`Sandbox Executor <sandbox>` hosted on Jina Hub. The Executor runs remotely on Jina Hub.       |
| ✅         | ❌      | `'docker://sentence-encoder'`                 | Use a pre-built Executor as a Docker container.                                                           |


````{admonition} Hint: Load multiple Executors from the same directory
:class: hint

You don't need to specify the parent directory for each Executor.
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
## External Executors

````{admonition} How-To chapter
:class: seealso
For a more detailed look at this feature, see our {ref}`how-to on external Executors <external-executor>`.
The also covers launching an Executor that can then be used as an External Executor in a Flow.
````

Usually a Flow starts and stops all of its own Executors.
However, external Executors are started and stopped by *other* Flows, meaning they can reside on any machine.

This is useful for sharing expensive Executors (like stateless, GPU-based encoders) between Flows.

Both {ref}`served and shared Executors <serve-executor-standalone>` can be used as external Executors.

When you add an external Executor to a Flow, you have to provide a `host` and `port`, and enable the `external` flag:

```python
from jina import Flow

Flow().add(host='123.45.67.89', port=12345, external=True)
```

The Flow doesn't start or stop this Executor and assumes that it is externally managed and available at `123.45.67.89:12345`.

You can also use external Executors with `tls`:

```python
from jina import Flow

Flow().add(host='123.45.67.89', port=443, external=True, tls=True)
```

```{hint} 
Using `tls` to connect to the External Executor is especially needed to use an external Executor deployed with JCloud. See the JCloud {ref}`documentation <jcloud-external-executors>`
for further details
```


(floating-executors)=
## Floating Executors

Some Executors in your Flow can be used for asynchronous background tasks that take time and don't generate a required output. For instance,
logging specific information in external services, storing partial results, etc.

You can unblock your Flow from such tasks by using *floating Executors*.

Normally, all Executors form a pipeline that handles and transforms a given request until it is finally returned to the Client.

However, floating Executors do not feed their outputs back into the pipeline. Therefore, the Executor's output does not affect the response for the Client, and the response can be returned without waiting for the floating Executor to complete its task.
 
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

In this example the response is returned without waiting for the floating Executor to complete. However, the Flow is not closed until
the floating Executor has handled the request.

You can plot the Flow and see the Executor is floating disconnected from the **Gateway**.

```{figure} flow_floating.svg
:width: 70%

```
A floating Executor can *never* come before a non-floating Executor in your Flow's {ref}`topology <flow-complex-topologies>`.

This leads to the following behaviors:

- **Implicit reordering**: When you add a non-floating Executor after a floating Executor without specifying its `needs` parameter, the non-floating Executor is chained after the previous non-floating one.
```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add()
f.plot()
```

```{figure} flow_middle_1.svg
:width: 70%

```

- **Chaining floating Executors**: To chain more than one floating Executor, you need to add all of them with the `floating` flag, and explicitly specify the `needs` argument.

```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add(needs=['middle'], floating=True)
f.plot()
```

```{figure} flow_chain_floating.svg
:width: 70%

```

- **Overriding the `floating` flag**: If you add a floating Executor as part of `needs` parameter of a non-floating Executor, then the floating Executor is no longer considered floating.

```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add(needs=['middle'])
f.plot()
```

```{figure} flow_cancel_floating.svg
:width: 70%

```


## Configure Executors
You can set and override {class}`~jina.Executor` configuration when adding them to a {class}`~jina.Flow`.

This example shows how to start a Flow with an Executor using the Python API:

```python
from jina import Flow

with Flow().add(
    uses='MyExecutor',
    uses_with={"parameter_1": "foo", "parameter_2": "bar"},
    py_modules=["executor.py"],
    uses_metas={
        "name": "MyExecutor",
        "description": "MyExecutor does a thing to the stuff in your Documents",
    },
    uses_requests={"/index": "my_index", "/search": "my_search", "/random": "foo"},
    workspace="some_custom_path",
) as f:
    ...
```

- `uses_with` is a key-value map that defines the {ref}`arguments of the Executor'<executor-args>` `__init__` method.
- `uses_requests` is a key-value map that defines the {ref}`mapping from endpoint to class method<executor-requests>`. This is useful to overwrite the default endpoint-to-method mapping defined in the Executor python implementation.
- `workspace` is a string that defines the {ref}`workspace <executor-workspace>`.
- `py_modules` is a list of strings that defines the Executor's Python dependencies;
- `uses_metas` is a key-value map that defines some of the Executor's {ref}`internal attributes<executor-metas>`. It contains the following fields:
    - `name` is a string that defines the name of the Executor;
    - `description` is a string that defines the description of this Executor. It is used in the automatic docs UI;

### Set `with` via `uses_with`

To set/override an Executor's `with` configuration, use `uses_with`. The `with` configuration refers to user-defined 
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
You can set/override an Executor's `requests` configuration and bind methods to custom endpoints. 
In the following code:

- We replace the endpoint `/foo` bound to the `foo()` function with both `/non_foo` and `/alias_foo`. 
- We add a new endpoint `/bar` for binding `bar()`. 

Note the `all_req()` function is bound to **all** endpoints except those explicitly bound to other functions, i.e. `/non_foo`, `/alias_foo` and `/bar`.

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

### Set `metas` via `uses_metas`

To set/override an Executor's `metas` configuration, use `uses_metas`:

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


## Unify output ndarray types

Different {class}`~jina.Executor`s in a {class}`~jina.Flow` may depend on different `types` for array-like data such as `doc.tensor` and `doc.embedding`,
often because they were written with different machine learning frameworks.
As the builder of a Flow you don't always have control over this, for example when using Executors from Jina Hub.

To ease the integration of different Executors, a Flow allows you to convert `tensor` and `embedding`
by using the `f.add(..., output_array_type=..)`:

```python
from jina import Flow

f = Flow().add(uses=MyExecutor, output_array_type='numpy').add(uses=NeedsNumpyExecutor)
```

This converts the `.tensor` and `.embedding` fields of all output Documents of `MyExecutor` to `numpy.ndarray`, making the data
usable by `NeedsNumpyExecutor`. This works whether `MyExecutor` populates these fields with arrays/tensors from
PyTorch, TensorFlow, or any other popular ML framework.

````{admonition} Output types
:class: note

`output_array_type=` supports more types than `'numpy'`. For the full specification and further details, check the
[protobuf serialization docs](https://docarray.jina.ai/fundamentals/document/serialization/#from-to-protobuf).
````

