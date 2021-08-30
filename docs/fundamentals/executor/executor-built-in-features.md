## Executor Features


### YAML Interface

An Executor can be loaded from and stored to a YAML file. The YAML file has the following format:

```yaml
jtype: MyExecutor
with:
  ...
metas:
  ...
requests:
  ...
```

- `jtype` is a string. Defines the class name, interchangeable with bang mark `!`;
- `with` is a map. Defines kwargs of the class `__init__` method
- `metas` is a dictionary. It defines the meta information of that class. It contains the following fields:
    - `name` is a string. Defines the name of the executor;
    - `description` is a string. Defines the description of this executor. It will be used in automatic docs UI;
    - `workspace` is a string. Defines the workspace of the executor;
    - `py_modules` is a list of strings. Defines the Python dependencies of the executor;
- `requests` is a map. Defines the mapping from endpoint to class method name;

### Load and Save Executor's YAML config

You can use class method `Executor.load_config` and object method `exec.save_config` to load and save YAML config:

```python
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


### Workspace

Executor's workspace is inherited according to the following rule (`OR` is a python `or`, i.e. first thing first, if NA
then second):

```{figure} ../../../.github/2.0/workspace-inherit.svg
:align: center
```

### Metas

The meta attributes of an `Executor` object are now gathered in `self.metas`, instead of directly posting them to `self`
, e.g. to access `name` use `self.metas.name`.

#### `.metas` & `.runtime_args`

By default, an `Executor` object contains two collections of attributes: `.metas` and `.runtime_args`. They are both
in `SimpleNamespace` type and contain some key-value information. However, they are defined differently and serve
different purposes.

- **`.metas` are statically defined.** "Static" means, e.g. from hard-coded value in the code, from a YAML file.
- **`.runtime_args` are dynamically determined during runtime.** Means that you don't know the value before running
  the `Executor`, e.g. `pea_id`, `replicas`, `replica_id`. Those values are often related to the system/network
  environment around the `Executor`, and less about the `Executor` itself.

In 2.0rc1, the following fields are valid for `metas` and `runtime_args`:

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

### Handle parameters

Parameters are passed to executors via `request.parameters` with `Flow.post(..., parameters=)`. This way all
the `executors` will receive
`parameters` as an argument to their `methods`. These `parameters` can be used to pass extra information or tune
the `executor` behavior for a given request without updating the general configuration.

```python
from typing import Optional
from jina import Executor, requests, DocumentArray, Flow


class MyExecutor(Executor):
    def __init__(self, default_param: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_param = default_param

    @requests
    def foo(self, docs: Optional[DocumentArray], parameters: dict, **kwargs):
        param = parameters.get('param', self.default_param)
        # param may be overriden for this specific request
        assert param == 5


with Flow().add(uses=MyExecutor) as f:
    f.post(on='/endpoint', inputs=DocumentArray([]), parameters={'param': 5})
```

However, this can be a problem when the user wants different executors to have different values of the same parameters.
In that case one can specify specific parameters for the specific `executor` by adding a `dictionary` inside parameters
with the `executor` name as `key`. Jina will then take all these specific parameters and copy to the root of the
parameters dictionary before calling the executor `method`.

```python
from typing import Optional
from jina import Executor, requests, DocumentArray, Flow


class MyExecutor(Executor):
    def __init__(self, default_param: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_param = default_param

    @requests
    def foo(self, docs: Optional[DocumentArray], parameters: dict, **kwargs):
        param = parameters.get('param', self.default_param)
        # param may be overriden for this specific request. 
        # The first instance will receive 10, and the second one will receive 5
        if self.metas.name == 'my-executor-1':
            assert param == 10
        elif self.metas.name == 'my-executor-2':
            assert param == 5


with (Flow().
        add(uses={'jtype': 'MyExecutor', 'metas': {'name': 'my-executor-1'}}).
        add(uses={'jtype': 'MyExecutor', 'metas': {'name': 'my-executor-2'}})) as f:
    f.post(on='/endpoint', inputs=DocumentArray([]), parameters={'param': 5, 'my-executor-1': {'param': 10}})
```