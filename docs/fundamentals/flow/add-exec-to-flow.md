# Add Executor


`.add()` is the core method to add an Executor to a `Flow` object. Each `add` creates a new Executor, and these
Executors can be run as a local thread/process, a remote process, inside a Docker container, or even inside a remote
Docker container.



## Chain `.add()`

Chaining `.add()`s creates a sequential Flow.

```python
from jina import Flow

f = Flow().add().add().add().add()
```

```{figure} ../../../.github/2.0/chain-flow.svg
:align: center
```

## Define Executor via `uses`

`uses` parameter to specify the Executor.

`uses` accepts multiple value types including class name, Docker image, (inline) YAML.
Therefore, you can add an executor via:

````{tab} Class Name

```python
from jina import Flow, Executor


class MyExecutor(Executor):
    ...


f = Flow().add(uses=MyExecutor)

with f:
    ...
```
````

`````{tab} YAML file
`myexec.py`:

```python
from jina import Executor


class MyExecutor(Executor):

    def __init__(self, bar, *args, **kwargs):
        super().__init__()
        self.bar = bar

    ...
```

`myexec.yml`

```yaml
jtype: MyExecutor
with:
  bar: 123
metas:
  name: awesomeness
  description: my first awesome executor
  py_modules: myexec.py
requests:
  /random_work: foo
```

```python
from jina import Flow

f = Flow().add(uses='myexec.yml')

with f:
    ...
```

````{admonition} Note
:class: note
YAML file can be also inline:

```python
from jina import Flow

f = (Flow()
     .add(uses='''
jtype: MyExecutor
with:
  bar: 123
metas:
  name: awesomeness
  description: my first awesome executor
requests:
  /random_work: foo    
    '''))
```
````
`````

````{tab} Dict
```python
from jina import Flow

f = Flow().add(
    uses={
        'jtype': 'MyExecutor',
        'with': {'bar': 123}
    })
```
````




## Add remote Executor

### Add an already spawned Executor

A Flow does not have to be local-only. You can use any Executor on remote(s). 

The external Executor in the following two use-cases could have been spawned

- either by another Flow
- or by the `jina executor` CLI command

```python
f.add(host='localhost', port_in=12345, external=True)
f.add(host='123.45.67.89', port_in=12345, external=True)
```

### [Spawn remote Executors using `JinaD`](../../advanced/daemon/remote-executors)

````{admonition} Commonly used arguments for deployment in 
:class: tip 

| Name | default | Description |
| --- | --- | --- |
| `host` | `0.0.0.0` | The host of the machine. Can be an ip address or DNS name (e.g. `0.0.0.0`, `my_encoder.jina.ai`) |
| `port_expose` | randomly initialized | Port of JinaD on the remote machine. |
| `port_in` | randomly initialized | Port for incoming traffic for the Executor. |
| `port_out` | randomly initialized | Port for outgoing traffic for the Executor. This is only used in the remote-local use-case described below. |
| `connect_to_predecessor` | `False` | Forces a Head to connect to the previous Tail. This is only used in the remote-local use-case described below. |
| `external` | `False` | Stops `Flow` from context managing an Executor. This allows spawning of an external Executor and reusing across multiple Flows. |
| `uses`, `uses_before` and `uses_after` prefix | No prefix | When prefixing one of the `uses` arguments with `docker` or `jinahub+docker`, the Executor does not run natively, but is spawned inside a container. |

````

````{admonition} See Also
:class: seealso
{ref}`JinaD <daemon-cookbook>`

{ref}`JinaHub <hub-cookbook>`
````


### Forcing an Executor in the remote-local config

Sometimes you want to use a remote Executor in your local Flow (e.g. using an expensive encoder on a remote GPU). Then
the remote cannot talk back to the next local Executor directly. This is similar to a server that cannot talk to a
client before the client has opened a connection. The Flow inside Jina has an auto-detection mechanism for such cases.
Anyhow, in some networking setups this mechanism fails. Then you can force this by hand by setting
the `connect_to_predecessor` argument and `port_out` to the Executor in front.

```python
f.add(name='remote', host='123.45.67.89', port_out=23456).add(name='local', connect_to_predecessor=True)
```

## Override Executor config

You can override an executor's meta configs when creating a flow.

### Override `metas` configuration
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
           pod0@219291[L]:ready and listening
        gateway@219291[L]:ready and listening
           Flow@219291[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:58827
	🔒 Private network:	192.168.1.101:58827
different_workspace
```


### Override `with` configuration
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
           pod0@219662[L]:ready and listening
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


### Override `requests` configuration
You can override the `requests` configuration of an executor and bind methods to endpoints that you provide:


```python
from jina import Executor, requests, Flow

class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print('foo')
    
    def bar(self, docs, **kwargs):
        print('bar')

flow = Flow().add(uses=MyExecutor, uses_requests={'/index': 'bar'})
with flow as f:
    f.post('/index')
    f.post('/dummy')
```

```text
           pod0@221058[L]:ready and listening
        gateway@221058[L]:ready and listening
           Flow@221058[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:36507
	🔒 Private network:	192.168.1.101:36507
	🌐 Public address:	197.28.82.165:36507
bar
foo
```

## Summary: common patterns


| Description | Usage (`f = Flow(...)`) |
| --- | --- |
| Local native Executor in the context |  `f.add(uses=MyExecutor)` |
| Local native Executor from a YAML | `f.add(uses='mwu_encoder.yml')` | 
| Executor from Jina Hub | `f.add(uses='jinahub://MyExecutor')` |
| Dockerized Executor from Jina Hub | `f.add(uses='jinahub+docker://MyExecutor')` |
| Generalized dockerized Executor | `f.add(uses='docker://MyExecutor')` |
| Existing remote Executor | `f.add(host='123.45.67.89', port_in=12345, external=True)` |
| Spawn Remote Executor (via `jinad` on Remote) | `f.add(uses='mwu_encoder.yml', host='123.45.67.89', port_in=12345, port_expose=8080)` |


For a full list of arguments, please check `jina executor --help`.

