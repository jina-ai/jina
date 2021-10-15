# Executor Features

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


## Use Executor out of Flow

`Executor` object can be used directly just like a regular Python object. For example,

```python
from jina import Executor, requests, DocumentArray, Document


class MyExec(Executor):

    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            d.text = 'hello world'


m = MyExec()
da = DocumentArray([Document(text='test')])
m.foo(da)
print(da)
```

```text
DocumentArray has 1 items:
{'id': '20213a02-bdcd-11eb-abf1-1e008a366d48', 'mime_type': 'text/plain', 'text': 'hello world'}
```

This is useful in debugging an Executor.

## Gracefully close Executor

You might need to execute some logic when your executor's destructor is called. For example, you want to
persist data to the disk (e.g. in-memory indexed data, fine-tuned model,...). To do so, you can overwrite the
method `close` and add your logic.

```{code-block} python
---
emphasize-lines: 11, 12
---
from jina import Executor, requests, Document, DocumentArray


class MyExec(Executor):

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(doc.text)

    def close(self):
        print("closing...")


with MyExec() as executor:
    executor.foo(DocumentArray([Document(text='hello world')]))
```

```text
hello world
closing...
```

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
- `requests` is a map. Defines the mapping from endpoint to class method name;

### Load and save Executor config

You can use class method `Executor.load_config` and object method `exec.save_config` to load and save YAML config:

```{code-block} python
---
emphasize-lines: 25, 26, 27
---
from jina import Executor


class MyExecutor(Executor):

    def __init__(self, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar

    def foo(self, **kwargs):
        pass


y_literal = """
jtype: MyExecutor
with:
  bar: 123
metas:
  name: awesomeness
  description: my first awesome executor
requests:
  /random_work: foo
"""

exec = Executor.load_config(y_literal)
exec.save_config('y.yml')
Executor.load_config('y.yml')
```

## Meta attributes

By default, an `Executor` object contains two collections of attributes: `.metas` and `.runtime_args`. They are both
in `SimpleNamespace` type and contain some key-value information. However, they are defined differently and serve
different purposes.

- **`.metas` are statically defined.** "Static" means, e.g. from hard-coded value in the code, from a YAML file.
- **`.runtime_args` are dynamically determined during runtime.** Means that you don't know the value before running
  the `Executor`, e.g. `pea_id`, `replicas`, `replica_id`. Those values are often related to the system/network
  environment around the `Executor`, and less about the `Executor` itself.

The following fields are valid for `metas` and `runtime_args`:

| Attribute | Fields |
| --- | --- |
| `.metas` (static values from hard-coded values, YAML config) | `name`, `description`, `py_modules`, `workspace` |
| `.runtime_args` (runtime values from its containers, e.g. `Runtime`, `Pea`, `Pod`) | `name`, `description`, `workspace`, `log_config`, `quiet`, `quiet_error`, `identity`, `port_ctrl`, `ctrl_with_ipc`, `timeout_ctrl`, `ssh_server`, `ssh_keyfile`, `ssh_password`, `uses`, `py_modules`, `port_in`, `port_out`, `host_in`, `host_out`, `socket_in`, `socket_out`, `memory_hwm`, `on_error_strategy`, `num_part`, `entrypoint`, `docker_kwargs`, `pull_latest`, `volumes`, `host`, `port_expose`, `quiet_remote_logs`, `upload_files`, `workspace_id`, `daemon`, `runtime_backend`, `runtime_cls`, `timeout_ready`, `env`, `expose_public`, `pea_id`, `pea_role`, `noblock_on_start`, `uses_before`, `uses_after`, `parallel`, `replicas`, `polling`, `scheduling`, `pod_role`, `peas_hosts`, `proxy`, `uses_metas`, `external`, `gpus`, `zmq_identity`, `hosts_in_connect`, `uses_with` |


````{admonition} Note
:class: note
The YAML API will ignore `.runtime_args` during save and load as they are not statically stored
````

````{admonition} Hint
:class: hint
For any other parametrization of the Executor, you can still access its constructor arguments (defined in the
class `__init__`) and the request `parameters`
````

````{admonition} Note
:class: note
`workspace` will be retrieved from either `metas` or `runtime_args`, in that order
````


## Workspace

Executor's workspace is inherited according to the following rule (`OR` is a python `or`, i.e. first thing first, if NA
then second):

```{figure} ../../../.github/2.0/workspace-inherit.svg
:align: center
```

(executor-request-parameters)=

