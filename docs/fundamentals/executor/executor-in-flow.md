# Executors inside a Flow

## YAML interface

An Executor can be loaded from and stored to a YAML file. The YAML file has the following format:

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
  index: MyExecutor_index_method
  search: MyExecutor_search_method
  random: MyExecutor_other_method
```

- `jtype` is a string. Defines the class name, interchangeable with bang mark `!`;
- `with` is a map. Defines kwargs of the class `__init__` method
- `metas` is a dictionary. It defines the meta information of that class. It contains the following fields:
    - `name` is a string. Defines the name of the executor;
    - `description` is a string. Defines the description of this executor. It will be used in automatic docs UI;
    - `workspace` is a string. Defines the workspace of the executor;
    - `py_modules` is a list of strings. Defines the Python dependencies of the executor;
- `requests` is a map. Defines the mapping from endpoint to class method name. Useful if one needs to overwrite the default methods


### Passing arguments

When using an Executor in a Flow, there are two ways of passing arguments to its `__init__`.

````{tab} via uses_with

```python
from jina import Flow

f = Flow.add(uses=MyExecutor, uses_with={'foo': 'hello', 'bar': 1})

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
from jina import Flow

f = Flow.add(uses='my-exec.yml')

with f:
  ...
```
````


`````


```{hint}

`uses_with` has higher priority than predefined `with` config in YAML. When both presented, `uses_with` is picked up first.

```


#### Pass/change request parameters

In this example, `MyExec2` receives the parameters `{'top_k': 10}` from `MyExec1` when the Flow containing `MyExec1 -> MyExec2` in order. 

```{code-block} python
---
emphasize-lines: 7, 13
---
from jina import requests, Document, Executor

class MyExec1(Executor):

    @requests(on='/index')
    def index(self, **kwargs):
        return {'top_k': 10}

class MyExec2(Executor):

    @requests(on='/index')
    def index(self, parameters, **kwargs):
        self.docs[:int(parameters['top_k']))
```

## Exception handling

Exception inside `@requests` decorated functions can be simply raised. The Flow will handle it.

```python
from jina import Executor, requests, Flow
from jina.types.request import Response


class MyExecutor(Executor):

    @requests
    def foo(self, **kwargs):
        raise NotImplementedError('no time for it')


f = Flow().add(uses=MyExecutor)


def print_why(resp: Response):
    print(resp.status.description)


with f:
    f.post('', on_error=print_why)
```

```console

       executor@47887[L]:ready and listening
        gateway@47887[L]:ready and listening
           Flow@47887[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:49242
	🔒 Private network:	192.168.178.31:49242
	🌐 Public address:	217.70.138.123:49242
       executor@47893[E]:NotImplementedError('no time for it')
 add "--quiet-error" to suppress the exception details
Traceback (most recent call last):
  File "/Users/hanxiao/Documents/jina/jina/peapods/runtimes/zmq/zed.py", line 250, in _msg_callback
    processed_msg = self._callback(msg)
  File "/Users/hanxiao/Documents/jina/jina/peapods/runtimes/zmq/zed.py", line 236, in _callback
    msg = self._post_hook(self._handle(self._pre_hook(msg)))
  File "/Users/hanxiao/Documents/jina/jina/peapods/runtimes/zmq/zed.py", line 203, in _handle
    peapod_name=self.name,
  File "/Users/hanxiao/Documents/jina/jina/peapods/runtimes/request_handlers/data_request_handler.py", line 163, in handle
    field='groundtruths',
  File "/Users/hanxiao/Documents/jina/jina/executors/__init__.py", line 200, in __call__
    self, **kwargs
  File "/Users/hanxiao/Documents/jina/jina/executors/decorators.py", line 105, in arg_wrapper
    return fn(*args, **kwargs)
  File "/Users/hanxiao/Documents/jina/toy43.py", line 9, in foo
    raise NotImplementedError('no time for it')
NotImplementedError: no time for it
NotImplementedError('no time for it')
```

### Multiple DocArrays as input
