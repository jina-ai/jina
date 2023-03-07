(flow-add-executors)=
# Add Executors

## Define Executor with `uses`

An {class}`~jina.Executor`'s type is defined by the `uses` keyword:

````{tab} Deployment
```python
from jina import Deployment

dep = Deployment(uses=MyExec)
```
````
````{tab} Flow
```python
from jina import Flow

f = Flow().add(uses=MyExec)
```
````

Note that some usages are not supported on JCloud due to security reasons and the nature of facilitating local debugging.

| Local Dev | JCloud | `uses=...`                              | Description                                                                                               |
|-----------|--------|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| ✅         | ❌      | `ExecutorClass`                               | Use `ExecutorClass` from the inline context.                                                              |
| ✅         | ❌      | `'my.py_modules.ExecutorClass'`               | Use `ExecutorClass` from `my.py_modules`.                                                                 |
| ✅         | ✅      | `'executor-config.yml'`                       | Use an Executor from a YAML file defined by {ref}`Executor YAML interface <executor-yaml-spec>`.          |
| ✅         | ❌      | `'jinaai://jina-ai/TransformerTorchEncoder/'`        | Use an Executor as Python source from Executor Hub.                                                           |
| ✅         | ✅      | `'jinaai+docker://jina-ai/TransformerTorchEncoder'`  | Use an Executor as a Docker container from Executor Hub.                                                      |
| ✅         | ✅      | `'jinaai+sandbox://jina-ai/TransformerTorchEncoder'` | Use a {ref}`Sandbox Executor <sandbox>` hosted on Executor Hub. The Executor runs remotely on Executor Hub.       |
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
dep = Deployment(extra_search_paths=['../executor']).add(uses='config1.yml')) # Deployment
f = Flow(extra_search_paths=['../executor']).add(uses='config1.yml').add(uses='config2.yml') # Flow
```

````


(flow-configure-executors)=
## Configure Executors
You can set and override {class}`~jina.Executor` configuration when adding them to an Orchestration.

This example shows how to start a Flow with an Executor using the Python API:

````{tab} Deployment
```python
from jina import Deployment

dep = Deployment(
    uses='MyExecutor',
    uses_with={"parameter_1": "foo", "parameter_2": "bar"},
    py_modules=["executor.py"],
    uses_metas={
        "name": "MyExecutor",
        "description": "MyExecutor does a thing to the stuff in your Documents",
    },
    uses_requests={"/index": "my_index", "/search": "my_search", "/random": "foo"},
    workspace="some_custom_path",
)

with dep:
    ...
```
````
````{tab} Flow
```python
from jina import Flow

f = Flow().add(
    uses='MyExecutor',
    uses_with={"parameter_1": "foo", "parameter_2": "bar"},
    py_modules=["executor.py"],
    uses_metas={
        "name": "MyExecutor",
        "description": "MyExecutor does a thing to the stuff in your Documents",
    },
    uses_requests={"/index": "my_index", "/search": "my_search", "/random": "foo"},
    workspace="some_custom_path",
) 

with f:
    ...
```
````

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

````{tab} Deployment
```python
from jina import Executor, requests, Deployment


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


dep = Deployment(uses=MyExecutor, uses_with={'param1': 10, 'param3': 30})

with dep:
    dep.post('/')
```
```text
      executor0@219662[L]:ready and listening
        gateway@219662[L]:ready and listening
           Deployment@219662[I]:🎉 Deployment is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:32825
	🔒 Private network:	192.168.1.101:32825
	🌐 Public address:	197.28.82.165:32825
param1: 10
param2: 2
param3: 30
```
````
````{tab} Flow
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


f = Flow().add(uses=MyExecutor, uses_with={'param1': 10, 'param3': 30})

with f:
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
````

### Set `requests` via `uses_requests`

You can set/override an Executor's `requests` configuration and bind methods to custom endpoints. 
In the following code:

- We replace the endpoint `/foo` bound to the `foo()` function with both `/non_foo` and `/alias_foo`. 
- We add a new endpoint `/bar` for binding `bar()`. 

Note the `all_req()` function is bound to **all** endpoints except those explicitly bound to other functions, i.e. `/non_foo`, `/alias_foo` and `/bar`.

````{tab} Deployment
```python
from jina import Executor, requests, Deployment


class MyExecutor(Executor):
    @requests
    def all_req(self, parameters, **kwargs):
        print(f'all req {parameters.get("recipient")}')

    @requests(on='/foo')
    def foo(self, parameters, **kwargs):
        print(f'foo {parameters.get("recipient")}')

    def bar(self, parameters, **kwargs):
        print(f'bar {parameters.get("recipient")}')


dep = Deployment(
    uses=MyExecutor,
    uses_requests={
        '/bar': 'bar',
        '/non_foo': 'foo',
        '/alias_foo': 'foo',
    },
)

with dep
    dep.post('/bar', parameters={'recipient': 'bar()'})
    dep.post('/non_foo', parameters={'recipient': 'foo()'})
    dep.post('/foo', parameters={'recipient': 'all_req()'})
    dep.post('/alias_foo', parameters={'recipient': 'foo()'})
```

```text
      executor0@221058[L]:ready and listening
        gateway@221058[L]:ready and listening
           Deployment@221058[I]:🎉 Deployment is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:36507
	🔒 Private network:	192.168.1.101:36507
	🌐 Public address:	197.28.82.165:36507
bar bar()
foo foo()
all req all_req()
foo foo()
```
````
````{tab} Flow
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


f = Flow().add(
    uses=MyExecutor,
    uses_requests={
        '/bar': 'bar',
        '/non_foo': 'foo',
        '/alias_foo': 'foo',
    },
)
with f:
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
````

### Set `metas` via `uses_metas`

To set/override an Executor's `metas` configuration, use `uses_metas`:

````{tab} Deployment
```python
from jina import Executor, requests, Deployment


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print(self.metas.name)


dep = Deployment(
    uses=MyExecutor,
    uses_metas={'name': 'different_name'},
)

with dep:
    dep.post('/')
```

```text
      executor0@219291[L]:ready and listening
        gateway@219291[L]:ready and listening
           Deployment@219291[I]:🎉 Deployment is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:58827
	🔒 Private network:	192.168.1.101:58827
different_name
```
````
````{tab} Flow
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
````

### Unify output `ndarray` types

Different {class}`~jina.Executor`s may depend on different `types` for array-like data such as `doc.tensor` and `doc.embedding`,
often because they were written with different machine learning frameworks.
As the builder of an Orchestration you don't always have control over this, for example when using Executors from Executor Hub.

To ease the integration of different Executors, a Flow allows you to convert `tensor` and `embedding`:


````{tab} Deployment
```python
from jina import Deployment

dep = Deployment(uses=MyExecutor, output_array_type='numpy').add(uses=NeedsNumpyExecutor)
```
````
````{tab} Flow
```python
from jina import Flow

f = Flow().add(uses=MyExecutor, output_array_type='numpy').add(uses=NeedsNumpyExecutor)
```
````

This converts the `.tensor` and `.embedding` fields of all output Documents of `MyExecutor` to `numpy.ndarray`, making the data
usable by `NeedsNumpyExecutor`. This works whether `MyExecutor` populates these fields with arrays/tensors from
PyTorch, TensorFlow, or any other popular ML framework.

````{admonition} Output types
:class: note

`output_array_type=` supports more types than `'numpy'`. For the full specification and further details, check the
[protobuf serialization docs](https://docarray.jina.ai/fundamentals/document/serialization/#from-to-protobuf).
````


(external-executors)=
## Add external Executors

Usually an Orchestration starts and stops its own Executor(s). External Executors are owned by *other* Orchestrations, meaning they can reside on any machine and their lifetime are controlled by others.

Using external Executors is useful for sharing expensive Executors (like stateless, GPU-based encoders) between Orchestrations.

Both {ref}`served and shared Executors <serve-executor-standalone>` can be used as external Executors.

When you add an external Executor, you have to provide a `host` and `port`, and enable the `external` flag:

````{tab} Deployment
```python
from jina import Deployment

Deployment(host='123.45.67.89', port=12345, external=True)

# or

Deployment(host='123.45.67.89:12345', external=True)
```
````
````{tab} Flow
```python
from jina import Flow

Flow().add(host='123.45.67.89', port=12345, external=True)

# or

Flow().add(host='123.45.67.89:12345', external=True)
```
````

The Orchestration doesn't start or stop this Executor and assumes that it is externally managed and available at `123.45.67.89:12345`.

Despite the lifetime control, the external Executor behaves just like a regular one. You can even add the same Executor to multiple Orchestrations.

### Enable TLS

You can also use external Executors with `tls`:

````{tab} Deployment
```python
from jina import Deployment

Deployment(host='123.45.67.89:443', external=True, tls=True)
```
````
````{tab} Flow
```python
from jina import Flow

Flow().add(host='123.45.67.89:443', external=True, tls=True)
```
````

After that, the external Executor behaves just like an internal one. You can even add the same Executor to multiple Orchestrations.

```{hint} 
Using `tls` to connect to the External Executor is especially needed to use an external Executor deployed with JCloud. See the JCloud {ref}`documentation <jcloud>` for further details
```

### Pass arguments

External Executors may require extra configuration to run. Think about an Executor that requires authentication to run. You can pass the `grpc_metadata` parameter to the Executor. `grpc_metadata` is a dictionary of key-value pairs to be passed along with every gRPC request sent to that Executor. 

````{tab} Deployment
```python
from jina import Deployment

Deployment(
    host='123.45.67.89',
    port=443,
    external=True,
    grpc_metadata={'authorization': '<TOKEN>'},
)
```
````
````{tab} Flow
```python
from jina import Flow

Flow().add(
    host='123.45.67.89',
    port=443,
    external=True,
    grpc_metadata={'authorization': '<TOKEN>'},
)
```
````

```{hint}
The `grpc_metadata` parameter here follows the `metadata` concept in gRPC. See [gRPC documentation](https://grpc.io/docs/what-is-grpc/core-concepts/#metadata) for details.
```
