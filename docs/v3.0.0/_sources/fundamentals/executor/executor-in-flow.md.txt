(executor-in-flow)=
# Executors inside a Flow

Executors are a good way to group your `DocumentArray` functions and logics into a class that can share `configuration` and `state` in a modular way.
However, the main advantage of using `Executor` is to be used in a `Flow` so that it can be served, scaled and deployed.

## Special Executor attributes

When implementing an `Executor`, if your executor overrides `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)`
                                 
```python
from jina import Executor


class MyExecutor(Executor):
    def __init__(self, foo: str, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
        self.foo = foo
```

This is important because when an `Executor` is instantiated in the context of a Flow, Jina is adding 3 extra arguments that are needed for the internal work of the `Executor`.
Some of these `arguments` can be of need when developing the internal logic of the Executor.

These `special` arguments are `metas`, `runtime_args` and `requests`.

### Metas

By default, an `Executor` object contains `.metas` as an attribute when loaded from the `Flow`. It is of `SimpleNamespace` type and contains some key-value information, 
that can be described statically in the description of the `Executor` inside a Flow.

The list of the `metas` are:

- `name`: Name given to the `Executor`
- `description`: Optional description of the Executor
- `py_modules`: List of python modules needed to import the Executor 
- `workspace`: Optional path to be used by the `Executor`


### Runtime args

By default, an `Executor` object contains `.runtime_args` as an attribute when loaded from the `Flow`. It is of `SimpleNamespace` type and contains some key-value information. 
As the name suggest, `runtime_args` are dynamically determined during runtime, meaning that you don't know the value before running the `Executor`. These values are often related to the system/network environment around the `Executor`, and less about the `Executor` itself, like shard_id` and `replicas`. They are usually set with the {meth}`~jina.orchestrate.flow.base.Flow.add` method.

The list of the `runtime_args` is:

- `name`: Name given to the `Executor`. This is dynamically adapted from the `name` in `metas` and depends on some additional arguments like `shard_id`. 
- `replicas`: Number of replicas of the same `Executor` deployed with the `Flow`.
- `shards`: Number of shards of the same `Executor` deployed with the `Flow`.
- `shard_id`: Identifier of the `shard` corresponding to the given `Executor` instance.
- `workspace`: Path to be used by the `Executor`. This is another way to pass a `workspace` to the `Executor` from the `Flow` ensuring that each `shard` gets a different one.
- `py_modules`: Path to the modules needed to import the `Executor`. This is another way to pass `py-modules` to the `Executor` from the `Flow`


````{admonition} Note
:class: note
The YAML API will ignore `.runtime_args` during save and load as they are not statically stored
````

### Requests
By default, an `Executor` object contains `.requests` as an attribute when loaded from the `Flow`. This attribute is a `Dict` describing the mapping between Executor methods and network endpoints: It holds endpoint strings as keys, and pointers to `function`s as values. 

### Workspace
Each `Executor` has a special `workspace` that is reserved for that specific `Executor` instance. The `workspace` property that can be used to extract the `path` to this workspace.

This `workspace` is generated using the workspace specified in `metas` or `runtime_args` workspace, plus adding special suffixes in case of sharded `Executor`s.

(executor-yaml-interface)=
## YAML interface

An Executor can be loaded from and stored to a YAML file. This YAML configuration can also be referenced or directly used inside a Flow YAML file.
 
 The YAML file has the following format:

```yaml
jtype: MyExecutor
with:
  parameter_1: foo
  parameter_2: bar
metas:
  name: MyExecutor
  description: "MyExecutor does a thing to the stuff in your Documents"
  workspace: workspace
  py_modules:
    - executor.py
requests:
  /index: MyExecutor_index_method
  /search: MyExecutor_search_method
  /random: MyExecutor_other_method
```

- `jtype` is a string. Defines the class name, interchangeable with bang mark `!`;
- `with` is a map. Defines `kwargs` of the class `__init__` method
- `metas` is a dictionary. It defines the meta information of that class. It contains the following fields:
    - `name` is a string. Defines the name of the executor;
    - `description` is a string. Defines the description of this executor. It will be used in automatic docs UI;
    - `workspace` is a string. Defines the workspace of the executor;
    - `py_modules` is a list of strings. Defines the Python dependencies of the executor;
- `requests` is a map. Defines the mapping from endpoint to class method name. Useful if one needs to overwrite the default endpoint-to-method mapping defined in the Executor python implementation.


### Passing arguments and overriding static arguments in the Flow

When using an Executor in a Flow, there are two ways of passing arguments to its `__init__`.


````{tab} via uses_with

```python
from jina import Executor, Flow


class MyExecutor(Executor):
    def __init__(self, foo, bar, **kwargs):
        super().__init__(**kwargs)
        self.foo = foo
        self.bar = bar


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
with:
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
        self.foo = foo
        self.bar = bar


f = Flow().add(uses='my-exec.yml')

with f:
    ...
```
````

`````

```{hint}
`uses_with` has higher priority than predefined `with` config in YAML. When both presented, `uses_with` is picked up first.
```

The same applies to `metas` and `requests`. You can define them statically inside the Executor definition YAML, or update their default values through `uses_metas` and `uses_requests`.

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
with:
  parameter_1: static_parameter_1
  parameter_2: static_parameter_2
metas:
  name: MyExecutor
  description: "MyExecutor does a thing to the stuff in your Documents"
  workspace: workspace
requests:
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
        'parameter_1': 'overriden_parameter_1',
        'parameter_2': 'overriden_parameter_2',
    },
    uses_metas={'name': 'Dynamic Name', 'workspace': 'overriden_worskpace'},
    uses_requests={'/index': 'foo', '/search': 'bar'},
)

print(f'\nStarting Flow with overriden Executor parameters')
with flow2:
    pass
```

```console
Starting Flow with default Executor parameters
⠋ 0/2 waiting executor0 gateway to be ready... 
parameter_1: static_parameter_1
parameter_2: static_parameter_2
metas: namespace(description='MyExecutor does a thing to the stuff in your Documents', name='MyExecutor', py_modules='', workspace='workspace')
requests: {'/default': <function MyExecutor.bar at 0x7fc3163f0710>, '/index': <function MyExecutor.default_fn at 0x7fc3163cc050>, '/search': <function MyExecutor.default_fn at 0x7fc3163cc050>}
           Flow@21607[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:53268
	🔒 Private network:	192.168.1.187:53268
	🌐 Public address:	212.231.186.65:53268

Starting Flow with overriden Executor parameters
⠋ 0/2 waiting executor0 gateway to be ready... 
parameter_1: overriden_parameter_1
parameter_2: overriden_parameter_2
metas: namespace(description='MyExecutor does a thing to the stuff in your Documents', name='Dynamic Name', py_modules='', workspace='overriden_worskpace')
requests: {'/index': <function MyExecutor.foo at 0x7fc3163ddb90>, '/search': <function MyExecutor.bar at 0x7fc3163f0710>}
           Flow@21607[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:58267
	🔒 Private network:	192.168.1.187:58267
	🌐 Public address:	212.231.186.65:58267
```

(pass-parameters)=
## Passing and changing request parameters

An important feature of `Executor`, beyond the capacity of *processing* Documents, is the capacity to receive `parameters` and to return additional results.

Results are returned inside the `parameters` dictionary, behind the reserved `__results__` key.

Note, however, that not all Executors or request methods populate this field with results. Some just modify the `Document`s passed to them, without adding further information.

In this example, `MyExec` receives the parameter `{'top_k': 10}` from the client, which can then be used internally.

It also exposes a `status` endpoint returning internal information in the form of a `dict`.

```python
from jina import requests, Executor, Flow


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


f = Flow().add(uses=MyExec, name='my_executor')


def print_response_parameters(resp):
    print(f' {resp.to_dict()["parameters"]}')


with f:
    f.post(on='/index', parameters={'top_k': 10}, inputs=[])
    f.post(on='/status', inputs=[], on_done=print_response_parameters)
```

```console
           Flow@27761[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:62128
	🔒 Private network:	192.168.1.187:62128
	🌐 Public address:	212.231.186.65:62128
Searching with top_k 10.0
 {'__results__': {'my_executor/rep-0': {'internal_parameter': 20.0}}}
```


## Exception handling

Exception inside `@requests` decorated functions can be simply raised. The Flow will handle it.

```python
from jina import Executor, requests, Flow


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError('no time for it')


f = Flow().add(uses=MyExecutor)


def print_why(resp):
    print(resp.status.description)


with f:
    f.post('', on_error=print_why)
```

```console
           Flow@28255[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:54317
	🔒 Private network:	192.168.1.187:54317
	🌐 Public address:	212.231.186.65:54317
executor0/rep-0@28271[E]:NotImplementedError('no time for it')
 add "--quiet-error" to suppress the exception details
Traceback (most recent call last):
  File "/home/joan/jina/jina/jina/serve/runtimes/worker/__init__.py", line 101, in process_data
    return await self._data_request_handler.handle(requests=requests)
  File "/home/joan/jina/jina/jina/serve/runtimes/request_handlers/data_request_handler.py", line 94, in handle
    field='docs',
  File "/home/joan/jina/jina/jina/serve/executors/__init__.py", line 224, in __acall__
    return await self.__acall_endpoint__(__default_endpoint__, **kwargs)
  File "/home/joan/jina/jina/jina/serve/executors/__init__.py", line 231, in __acall_endpoint__
    return await run_in_threadpool(func, self._thread_pool, self, **kwargs)
  File "/home/joan/jina/jina/jina/helper.py", line 1200, in run_in_threadpool
    executor, functools.partial(func, *args, **kwargs)
  File "/usr/lib/python3.7/concurrent/futures/thread.py", line 57, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/home/joan/jina/jina/jina/serve/executors/decorators.py", line 115, in arg_wrapper
    return fn(*args, **kwargs)
  File "/home/joan/jina/jina/toy.py", line 8, in foo
    raise NotImplementedError('no time for it')
NotImplementedError: no time for it
NotImplementedError('no time for it')
```

## Gracefully closing an Executor

You might need to execute some logic when your executor's destructor is called. For example, you want to
persist data to the disk (e.g. in-memory indexed data, fine-tuned model,...). To do so, you can overwrite the
method `close` and add your logic.

Jina will make sure that the `close` method is executed when the `Executor` is terminated inside a Flow or when deployed in any cloud-native environment.

One can think of this as `Jina` using the `Executor` as a context manager, making sure that the `close` method is always executed.

```python
from docarray import Document, DocumentArray
from jina import Flow, Executor, requests


class MyExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(doc.text)

    def close(self):
        print("closing...")


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

## Multiple DocumentArrays as input

We have seen that `Executor` methods can receive 3 types of parameters: `docs`, `parameters` and `docs_matrix`.

`docs_matrix` is a parameter that is only used in some special cases, for instance when an `Executor` receives messages from more than one `upstream` Executor
in the `Flow`.

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
    .add(uses=MergeExec, needs=['exec1', 'exec2'])
)

with f:
    returned_docs = f.post(on='/', inputs=DocumentArray.empty(1), return_results=True)

print(f'Resulting documents {returned_docs[0].text}')
```

```console
           Flow@1244[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:54550
	🔒 Private network:	192.168.1.187:54550
	🌐 Public address:	212.231.186.65:54550
MergeExec processing pairs of Documents "Exec1" and "Exec2"
Resulting documents Document merging from "Exec1" and "Exec2"
```

