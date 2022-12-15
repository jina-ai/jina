(executor-in-flow)=
# Executors inside a Flow

Executors are a way to group your `DocumentArray` functions and processing logic into a class that can share configuration and state in a modular way.
The main advantage of `Executor`s is using them in a `Flow`, which can serve, scale, and deploy them with ease.

(executor-api)=
## YAML and Python API

An Executor can be loaded from a YAML file or via Python API. 

````{dropdown} executor.py
:open:

This is a basic Executor, defined in its own file. Notice that there are no {ref}`request bindings <executor-requests>`. If an Executor is used in a Flow, these bindings can be configured via the Python or YAML Flow syntax, so each Flow can use the Executor in its own way. However, the standard way of adding `@requests` in the Executor itself would still work just fine.

```python
from jina import Executor
from docarray import DocumentArray


class MyExecutor(Executor):
    def __init__(self, parameter_1, parameter_2, **kwargs):
        super().__init__(**kwargs)
        print(f'parameter_1 = {parameter_1}')
        print(f'parameter_2 = {parameter_2}')

    def my_index(self, docs: DocumentArray, **kwargs):
        print('in my_index, bound to /index')

    def my_search(self, docs: DocumentArray, **kwargs):
        print('in my_search, bound to /search')

    def foo(self, docs: DocumentArray, **kwargs):
        print('in foo, bound to /random')
```

````

This YAML configuration can also be referenced or directly used inside a Flow YAML.
The YAML file has the following format:

````{tab} via Python API

This example shows how to start a Flow with an Executor via the Python API:

```python
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

Python API-specific options:

- `uses` can be a class or string that defines the Executor to load. You can also run Executors available on [Jina Hub](https://hub.jina.ai) with a {ref}`special syntax <use-hub-executor>`.

````

````{tab} via YAML

```yaml
  jtype: MyExecutor
  uses_with:
    parameter_1: foo
    parameter_2: bar
  uses_metas:
    name: MyExecutor
    description: "MyExecutor does a thing to the stuff in your Documents"
    py_modules:
      - executor.py
  uses_requests:
    /index: MyExecutor_index_method
    /search: MyExecutor_search_method
    /random: MyExecutor_other_method
  workspace: some_custom_path
```

YAML-specific options:

- `jtype` is a string that defines the class name, interchangeable with bang mark `!`;

````

Common arguments for both YAML and Python API:

- `uses_with` is a key-value map that defines the {ref}`arguments of the Executor'<executor-args>` `__init__` method.
- `uses_metas` is a key-value map that defines some {ref}`internal attributes<executor-metas>` of the Executor. It contains the following fields:
    - `name` is a string that defines the name of the executor;
    - `description` is a string that defines the description of this executor. It will be used in automatic docs UI;
    - `py_modules` is a list of strings that defines the Python dependencies of the executor;
- `uses_requests` is a key-value map that defines the {ref}`mapping from endpoint to class method<executor-requests>`. Useful if one needs to overwrite the default endpoint-to-method mapping defined in the Executor python implementation.
- `workspace` is a string value that defines the {ref}`workspace <executor-workspace>`.


(executor-args)=
### Passing and overriding arguments

When using an Executor in a Flow, there are two ways of passing arguments.

````{tab} via uses_with

```python
from jina import Executor, Flow


class MyExecutor(Executor):
    def __init__(self, foo, bar, **kwargs):
        super().__init__(**kwargs)
        print(f'foo = {foo}')
        print(f'bar = {bar}')


f = Flow().add(uses=MyExecutor, uses_with={'foo': 'hello', 'bar': 1})

with f:
    ...
```
````

`````{tab} via predefined YAML

````{dropdown} my-exec.yml
:open:

```yaml
jtype: MyExecutor
uses_with:
  foo: hello
  bar: 1
```
````

````{dropdown} my-flow.py
:open:

```python
from jina import Executor, Flow


class MyExecutor(Executor):
    def __init__(self, foo, bar, **kwargs):
        super().__init__(**kwargs)
        print(f'foo = {foo}')
        print(f'bar = {bar}')


f = Flow().add(uses='my-exec.yml')

with f:
    ...
```
````

`````

```{hint}
`uses_with` in Python API has higher priority than predefined `uses_with` config in YAML.
```

The same applies to `uses_metas` and `uses_requests`. You can define them statically inside the Executor definition YAML, or update their default values through `uses_metas` and `uses_requests` in Python API.

````{dropdown} Example

```python
from jina import Executor, requests, Flow


class MyExecutor(Executor):
    def __init__(self, parameter_1, parameter_2, **kwargs):
        super().__init__(**kwargs)
        self.parameter_1 = parameter_1
        self.parameter_2 = parameter_2
        print(
            f' \nparameter_1: {parameter_1}\nparameter_2: {parameter_2}\nmetas: {self.metas}\nrequests: {self.requests}'
        )

    @requests(on='/default')
    def default_fn(self, **kwargs):
        pass

    @requests
    def foo(self, **kwargs):
        pass

    @requests
    def bar(self, **kwargs):
        pass


exec_yaml = """ 
jtype: MyExecutor
uses_with:
  parameter_1: static_parameter_1
  parameter_2: static_parameter_2
uses_metas:
  name: MyExecutor
  description: "MyExecutor does a thing to the stuff in your Documents"
uses_requests:
  /index: default_fn
  /search: default_fn
"""

flow1 = Flow().add(uses=exec_yaml)

print(f'\nStarting Flow with default Executor parameters')
with flow1:
    pass

flow2 = Flow().add(
    uses=exec_yaml,
    uses_with={
        'parameter_1': 'overridden_parameter_1',
        'parameter_2': 'overridden_parameter_2',
    },
    uses_metas={'name': 'Dynamic Name'},
    workspace='workspace',
    uses_requests={'/index': 'foo', '/search': 'bar'},
)

print(f'\nStarting Flow with overriden Executor parameters')
with flow2:
    pass
```

```console
[...]
parameter_1: static_parameter_1
parameter_2: static_parameter_2
metas: namespace(description='MyExecutor does a thing to the stuff in your Documents', name='MyExecutor', py_modules='', workspace='workspace')
requests: {'/default': <function MyExecutor.bar at 0x7fc3163f0710>, '/index': <function MyExecutor.default_fn at 0x7fc3163cc050>, '/search': <function MyExecutor.default_fn at 0x7fc3163cc050>}

[...]
parameter_1: overriden_parameter_1
parameter_2: overriden_parameter_2
metas: namespace(description='MyExecutor does a thing to the stuff in your Documents', name='Dynamic Name', py_modules='', workspace='overriden_worskpace')
requests: {'/index': <function MyExecutor.foo at 0x7fc3163ddb90>, '/search': <function MyExecutor.bar at 0x7fc3163f0710>}
[...]
```


````


## Internal Executor attributes

When implementing an `Executor`, if your Executor overrides `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)`
                                 
```python
from jina import Executor


class MyExecutor(Executor):
    def __init__(self, foo: str, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
        self.foo = foo
```

This is important because when an `Executor` is instantiated in the context of a Flow, Jina is adding extra arguments.
Some of these `arguments` can be used when developing the internal logic of the Executor.

These `special` arguments are `workspace`, `requests`, `metas`, `runtime_args`.

(executor-workspace)=
### `workspace`

Each `Executor` has a special *workspace* that is reserved for that specific Executor instance.
The `.workspace` property contains the path to this workspace.

This `workspace` is based on the workspace passed when adding the Executor: `flow.add(..., workspace='path/to/workspace/')`.
The final `workspace` is generated by appending `'/<executor_name>/<shard_id>/'`.

This can be provided to the Executor via the {ref}`Python or YAML API <executor-api>`.

`````{dropdown} Default workspace

If the user hasn't provided a workspace, the Executor uses a default workspace, which is defined in the `JINA_DEFAULT_WORKSPACE_BASE`
environment variable.

````{admonition} Caution
:class: caution
After you install jina, the `JINA_DEFAULT_WORKSPACE_BASE` environment variable will be set in your `.bashrc`, `.zshrc`, or
`.fish` file.

To change the default Executor workspace on your system, you can change the value of this environment variable.
However, if you directly edit the corresponding command in your `.bashrc` (or `.zshrc`/`.fish`) file, your changes will be reverted the next time
you install jina on your system.

Instead, you can add `export JINA_DEFAULT_WORKSPACE_BASE=$YOUR_WOKSPACE` after the `# JINA_CLI_END` comment.
````

`````

(executor-requests)=
### `requests`

By default, an `Executor` object contains `.requests` as an attribute when loaded from the `Flow`. This attribute is a `Dict` describing the mapping between Executor methods and network endpoints: It holds endpoint strings as keys, and pointers to functions as values. 

These can be provided to the Executor via the {ref}`Python or YAML API <executor-api>`.

(executor-metas)=
### `metas`

An `Executor` object contains `.metas` as an attribute when loaded from the `Flow`. It is of [`SimpleNamespace`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) type and contains some key-value information. 

The list of the `metas` are:

- `name`: Name given to the `Executor`
- `description`: Optional description of the Executor
- `py_modules`: List of Python modules needed to import the Executor

These can be provided to the Executor via the {ref}`Python or YAML API <executor-api>`.

### `runtime_args`

By default, an `Executor` object contains `.runtime_args` as an attribute when loaded from the `Flow`. It is of [`SimpleNamespace`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) type and contains information in key-value format. 
As the name suggests, `runtime_args` are dynamically determined during runtime, meaning that you don't know the value before running the `Executor`. These values are often related to the system/network environment around the `Executor`, and less about the `Executor` itself, like `shard_id` and `replicas`. They are usually set with the {meth}`~jina.orchestrate.flow.base.Flow.add` method.

The list of the `runtime_args` is:

- `name`: Name given to the `Executor`. This is dynamically adapted from the `name` in `metas` and depends on some additional arguments like `shard_id`. 
- `replicas`: Number of {ref}`replicas <replicate-executors>` of the same `Executor` deployed with the `Flow`.
- `shards`: Number of {ref}`shards <partition-data-by-using-shards>` of the same `Executor` deployed with the `Flow`.
- `shard_id`: Identifier of the `shard` corresponding to the given `Executor` instance.
- `workspace`: Path to be used by the `Executor`. Note that the actual workspace directory used by the Executor is obtained by appending `'/<executor_name>/<shard_id>/'` to this value.
- `py_modules`: Path to the modules needed to import the `Executor`. This is another way to pass `py-modules` to the `Executor` from the `Flow`

These can **not** be provided by the user through any API. They are generated by the Flow orchestration.

(pass-parameters)=
## Passing and changing request parameters

An important feature of `Executor`, beyond the capacity of *processing* Documents, is the capacity to receive `parameters` and to return additional results.

Results are returned inside the `parameters` dictionary, behind the reserved `__results__` key.

Note, however, that not all Executors or request methods populate this field with results. Some just modify the `Document`s passed to them, without adding further information.

In this example, `MyExec` receives the parameter `{'top_k': 10}` from the client, which can then be used internally.

It also exposes a `status` endpoint returning internal information in the form of a `dict`.

```python
from jina import requests, Executor


class MyExec(Executor):
    def __init__(self, parameter=20, **kwargs):
        super().__init__(**kwargs)
        self.parameter = parameter

    @requests(on='/status')
    def status(self, **kwargs):
        return {'internal_parameter': self.parameter}

    @requests(on='/index')
    def search(self, parameters, **kwargs):
        print(f'Searching with top_k {parameters["top_k"]}')
        pass
```


````{dropdown} Example usage and output

```python
f = Flow().add(uses=MyExec, name='my_executor')


def print_response_parameters(resp):
    print(f' {resp.to_dict()["parameters"]}')


with f:
    f.post(on='/index', parameters={'top_k': 10}, inputs=[])
    f.post(on='/status', inputs=[], on_done=print_response_parameters)
```

```console
[...]
Searching with top_k 10.0
 {'__results__': {'my_executor/rep-0': {'internal_parameter': 20.0}}}
```

````

## Exception handling

Exceptions raised inside `@requests`-decorated functions can simply be raised. The Flow will handle it.

```python
from jina import Executor, requests, Flow


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError('no time for it')
```

````{dropdown} Example usage and output

```python
from jina import Flow
from executor import MyExecutor

f = Flow().add(uses=MyExecutor)


def print_why(resp, exception):
    print(resp.status.description)


with f:
    f.post('', on_error=print_why)
```

```console
[...]
executor0/rep-0@28271[E]:NotImplementedError('no time for it')
 add "--quiet-error" to suppress the exception details
[...]
  File "/home/joan/jina/jina/jina/serve/executors/decorators.py", line 115, in arg_wrapper
    return fn(*args, **kwargs)
  File "/home/joan/jina/jina/toy.py", line 8, in foo
    raise NotImplementedError('no time for it')
NotImplementedError: no time for it
NotImplementedError('no time for it')
```

````

## Graceful shutdown of an Executor

You might need to execute some logic when your Executor's destructor is called.
For example, you want to persist data to the disk (e.g. in-memory indexed data, fine-tuned model,...). 
To do so, you can overwrite the `close` method and add your logic.

Jina will make sure that the `close` method is executed when the `Executor` is terminated inside a Flow or when deployed in any cloud-native environment.

You can think of this as `Jina` using the `Executor` as a context manager, making sure that the `close` method is always executed.

```python
from jina import Executor, requests


class MyExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(doc.text)

    def close(self):
        print("closing...")
```

````{dropdown} Usage

```python
from jina import DocumentArray, Document, Flow

with MyExec() as executor:
    executor.foo(DocumentArray([Document(text='hello world')]))

f = Flow().add(uses=MyExec)

with f:
    f.post(inputs=DocumentArray([Document(text='hello world')]))
```

```console
Using MyExec as a context manager
hello world
closing...
Using MyExec in the Flow
           Flow@30104[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:54787
	🔒 Private network:	192.168.1.203:54787
	🌐 Public address:	212.231.186.65:54787
hello world
closing...

Process finished with exit code 0
```

````

## Multiple DocumentArrays as input

You have seen that `Executor` methods can receive three types of parameters: `docs`, `parameters` and `docs_matrix`.

`docs_matrix` is a parameter that is only used in some special cases.
One case is when an Executor receives messages from more than one upstream Executor in the Flow.

Let's see an example:

```python
from docarray import Document, DocumentArray
from jina import Flow, Executor, requests


class Exec1(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec1'


class Exec2(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec2'


class MergeExec(Executor):
    @requests
    def foo(self, docs_matrix, **kwargs):
        documents_to_return = DocumentArray()
        for doc1, doc2 in zip(*docs_matrix):
            print(
                f'MergeExec processing pairs of Documents "{doc1.text}" and "{doc2.text}"'
            )
            documents_to_return.append(
                Document(text=f'Document merging from "{doc1.text}" and "{doc2.text}"')
            )
        return documents_to_return


f = (
    Flow()
    .add(uses=Exec1, name='exec1')
    .add(uses=Exec2, name='exec2')
    .add(uses=MergeExec, needs=['exec1', 'exec2'], disable_reduce=True)
)

with f:
    returned_docs = f.post(on='/', inputs=DocumentArray.empty(1))

print(f'Resulting documents {returned_docs[0].text}')
```

````{dropdown} Output

```console
           Flow@1244[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:54550
	🔒 Private network:	192.168.1.187:54550
	🌐 Public address:	212.231.186.65:54550
MergeExec processing pairs of Documents "Exec1" and "Exec2"
Resulting documents Document merging from "Exec1" and "Exec2"
```

````

