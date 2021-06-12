Document, Executor, and Flow are the three fundamental concepts in Jina.

- [**Document**](Document.md) is the basic data type in Jina;
- [**Executor**](Executor.md) is how Jina processes Documents;
- [**Flow**](Flow.md) is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

---

# Cookbook on `Flow` 2.0 API

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [Minimum working example](#minimum-working-example)
  - [Pure Python: All-in-one Style](#pure-python-all-in-one-style)
  - [Pure Python: Flow-as-a-Service Style](#pure-python-flow-as-a-service-style)
  - [With YAML](#with-yaml)
- [`Flow` API](#flow-api)
  - [Create a Flow](#create-a-flow)
  - [Use a Flow](#use-a-flow)
  - [Visualize a Flow](#visualize-a-flow)
  - [Add `Executor` to a Flow](#add-executor-to-a-flow)
    - [Chain `.add()`](#chain-add)
    - [Define What Executor to Use via `uses`](#define-what-executor-to-use-via-uses)
    - [Intra Parallelism via `needs`](#intra-parallelism-via-needs)
    - [Inter Parallelism via `parallel`](#inter-parallelism-via-parallel)
    - [Add a Remote `Executor` via `host`](#add-a-remote-executor-via-host)
  - [Send Data Request via `post`](#send-data-request-via-post)
    - [Function Signature](#function-signature)
    - [Define Data via `inputs`](#define-data-via-inputs)
    - [Callback Functions](#callback-functions)
    - [Send Parameters](#send-parameters)
  - [Asynchronous Flow](#asynchronous-flow)
- [Flow as a Service](#flow-as-a-service)
  - [Python Client with gRPC Request](#python-client-with-grpc-request)
  - [Switch REST & gRPC Request](#switch-rest--grpc-request)
  - [`curl` with HTTP Request](#curl-with-http-request)
  - [Python Client with REST Request](#python-client-with-rest-request)
  - [Extend FastAPI interface](#extend-fastapi-interface)
- [Remarks](#remarks)
  - [Joining/Merging](#joiningmerging)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum working example

### Pure Python: All-in-one Style 

```python
from jina import Flow, Document, Executor, requests


class MyExecutor(Executor):

    @requests('/bar')
    def foo(self, docs):
        print(docs)


f = Flow().add(name='myexec1', uses=MyExecutor)

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```

### Pure Python: Flow-as-a-Service Style

Server:
```python
from jina import Flow, Executor, requests


class MyExecutor(Executor):

    @requests('/bar')
    def foo(self, docs):
        print(docs)


f = Flow(port_expose=12345).add(name='myexec1', uses=MyExecutor)

with f:
    f.block()
```

Client:
```python
from jina import Client, Document

c = Client(port_expose=12345)
c.post(on='/bar', inputs=Document(), on_done=print)
```


### With YAML

`my.yml`:

```yaml
jtype: Flow
executors:
  - name: myexec1
    uses: MyExecutor
```

```python
from jina import Flow, Document

f = Flow.load_config('my.yml')

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```

## `Flow` API

- Flow is how Jina streamlines and scales Executors. 
- Flow is a service, allowing multiple clients to access it via gRPC/REST/WebSocket from the public/private network.
  
A `Flow` object has the following common methods:

| |  |
|---|---|
|Construct Flow| `.add()`, `.needs()` |
|Run Flow| `with` context manager |
|Visualize Flow| `.plot()` |
|Send Request| `.post()`|
|Control| `.block()`, `.use_grpc_gateway()`, `.use_rest_gateway()` |

### Create a Flow

An empty Flow can be created via:

```python
from jina import Flow

f = Flow()
```

### Use a Flow

To use `f`, always open it as a content manager, just like you open a file. This is considered the best practice in
Jina:

```python
with f:
    ...
```

Note that,

- Flow follows a lazy construction pattern: it won't actually run until you use `with` to open it.
- Once a Flow is open via `with`, you can send data requests to it. However, you cannot change its construction
  via `.add()` any more until it leaves the `with` context.
- The context exits when its inner code is finished. A Flow's context without inner code will immediately exit. To
  prevent that, use `.block()` to suspend the current process.

  ```python
  with f:
      f.block()  # block the current process
  ```

### Visualize a Flow

```python
from jina import Flow

f = Flow().add().plot('f.svg')
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/2.0/empty-flow.svg?raw=true"/>

In Jupyter Lab/Notebook, the `Flow` object is rendered automatically without needing to call `plot()`.

### Add `Executor` to a Flow

`.add()` is the core method to add an Executor to a `Flow` object. Each `add` creates a new Executor, and these Executors
can be run as a local thread/process, a remote process, inside a Docker container, or even inside a remote Docker
container.

`.add()` accepts the following common arguments:

| |  |
|---|---|
|Define Executor| `uses`|
|Define Dependencies | `needs` |
|Parallelization | `parallel`, `polling` |

For a full list of arguments, please check `jina executor --help`.

#### Chain `.add()`

Chaining `.add()`s creates a sequential Flow.

```python
from jina import Flow

f = Flow().add().add().add().add()
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/2.0/chain-flow.svg?raw=true"/>

#### Define What Executor to Use via `uses`

`uses` parameter to specify the [Executor](Executor.md).

`uses` accepts multiple value types including class name, Docker image, (inline) YAML.

##### Add Executor via its Class Name

```python
from jina import Flow, Executor


class MyExecutor(Executor):
    ...


f = Flow().add(uses=MyExecutor)

with f:
    ...
```

##### Add Executor via YAML file

`myexec.py`:

```python
from jina import Executor


class MyExecutor(Executor):

    def __init__(self, bar):
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

Note that, YAML file can be also inline:

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

##### Add Executor via `Dict`

```python
from jina import Flow

f = Flow().add(
    uses={
        'jtype': 'MyExecutor',
        'with': {'bar': 123}
    })
```

##### Add Executor via Docker Image

To add an Executor from a Docker image tag `myexec:latest`, use:

```python
from jina import Flow

f = Flow().add(uses='docker://myexec:latest')
```

Once built, it will start a Docker container.

#### Intra Parallelism via `needs`

For parallelism, use the `needs` parameter:

```python
from jina import Flow

f = (Flow()
     .add(name='p1', needs='gateway')
     .add(name='p2', needs='gateway')
     .add(name='p3', needs='gateway')
     .needs(['p1', 'p2', 'p3'], name='r1'))
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-plot3.svg?raw=true"/>

`p1`, `p2`, `p3` now subscribe to `Gateway` and conduct their work in parallel. The last `.needs()` blocks all Executors
until they finish their work.

`.needs()` is syntax sugar and roughly equal to:

```python
.add(needs=['p1', 'p2', 'p3'])
```

`.needs_all()` is syntax sugar and roughly equal to:

```python
.add(needs=[all_orphan_executors_so_far])
```

"Orphan" Executors have no connected Executors to their outputs. The above code snippet can be also written as:

```python
from jina import Flow

f = (Flow()
     .add(name='p1', needs='gateway')
     .add(name='p2', needs='gateway')
     .add(name='p3', needs='gateway')
     .needs_all())
```

#### Inter Parallelism via `parallel`

Parallelism can also be performed inside an Executor using `parallel`. The example below starts three `p1`:

```python
from jina import Flow

f = (Flow()
     .add(name='p1', parallel=3)
     .add(name='p2'))
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/2.0/parallel-explain.svg?raw=true"/>

Note, by default:

- only one `p1` will receive a message.
- `p2` will be called when *any one of* `p1` finished.

To change that behavior, you can add `polling` argument to `.add()`, e.g. `.add(parallel=3, polling='ALL')`.
Specifically,

| `polling` | Who will receive from upstream? | When will downstream be called? | 
| --- | --- | --- |
| `ANY` | one of parallels | one of parallels is finished |
| `ALL` | all parallels | all parallels are finished |
| `ALL_ASYNC` | all parallels | one of parallels is finished |

You can combine inter and inner parallelization via:

```python
from jina import Flow

f = (Flow()
     .add(name='p1', needs='gateway')
     .add(name='p2', needs='gateway')
     .add(name='p3', parallel=3)
     .needs(['p1', 'p3'], name='r1'))
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-plot4.svg?raw=true"/>

#### Add a Remote `Executor` via `host`

A Flow does not have to be local-only. You can put any Executor to remote(s). In the example below, the Executor with the `host`
keyword `gpu-exec`, is put to a remote machine for parallelization, whereas other Executors stay local. Extra file
dependencies that need to be uploaded are specified via the `upload_files` keyword.

<table>
    <tr>
    <td>123.456.78.9</td>
    <td>

```bash
# have docker installed
docker run --name=jinad --network=host -v /var/run/docker.sock:/var/run/docker.sock jinaai/jina:latest-daemon --port-expose 8000
# stop the docker container
docker rm -f jinad
```

</td>
</tr>
  <tr>
    <td>
    Local
    </td>
    <td>

```python
from jina import Flow

f = (Flow()
     .add()
     .add(name='gpu_exec',
          uses='mwu_encoder.yml',
          host='123.456.78.9:8000',
          parallel=2,
          upload_files=['mwu_encoder.py'])
     .add())
```

</tr>

</table>

### Send Data Request via `post`

`.post()` is the core method for sending data to a `Flow` object.

`.post()` must be called *inside* the `with` context:

```python
from jina import Flow

f = Flow().add(...)

with f:
    f.post(...)
```

#### Function Signature

```python
def post(
        self,
        on: str,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        parameters: Optional[dict] = None,
        target_peapod: Optional[str] = None,
        **kwargs,
) -> None:
    """Post a general data request to the Flow.
  
    :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
    :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
    :param on_done: the function to be called when the :class:`Request` object is resolved.
    :param on_error: the function to be called when the :class:`Request` object is rejected.
    :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
    :param target_peapod: a regex string represent the certain peas/pods request targeted
    :param parameters: the kwargs that will be sent to the executor
    :param kwargs: additional parameters
    :return: None
    """
```

Compared to 1.x Client/Flow API, the three new arguments are:

- `on`: the endpoint used for identifying the user-defined `request_type`, labeled by `@requests(on='/foo')` in
  the `Executor` class;
- `parameters`: the kwargs that will be sent to the `Executor`;
- `target_peapod`: a regex string represent the certain peas/pods request targeted.

Note, all 1.x CRUD methods (`index`, `search`, `update`, `delete`) are just sugary syntax of `post` with `on='/index'`
, `on='/search'`, etc. Precisely, they are defined as:

```python
index = partialmethod(post, '/index')
search = partialmethod(post, '/search')
update = partialmethod(post, '/update')
delete = partialmethod(post, '/delete')
```

#### Define Data via `inputs`

`inputs` can take a single `Document` object, an iterator of `Document`, a generator of `Document`, a `DocumentArray`
object, and None.

For example:

```python
from jina import Flow, DocumentArray, Document

d1 = Document(content='hello')
d2 = Document(content='world')


def doc_gen():
    for j in range(10):
        yield Document(content=f'hello {j}')


with Flow() as f:
    f.post('/', d1)  # Single document

    f.post('/', [d1, d2])  # a list of Document

    f.post('/', doc_gen)  # Document generator

    f.post('/', DocumentArray([d1, d2]))  # DocumentArray

    f.post('/')  # empty
```

`Document` module provides some methods that lets you build `Document` generator, e.g. [`from_csv`
, `from_files`, `from_ndarray`, `from_ndjson`](Document.md#construct-from-json-csv-ndarray-and-files). They can be used
 in conjunction with `.post()`, e.g.

```python
from jina import Flow
from jina.types.document.generators import from_csv

f = Flow()

with f, open('my.csv') as fp:
    f.index(from_csv(fp, field_resolver={'question': 'text'}))
```

#### Callback Functions

Once a request is made, callback functions are fired. Jina Flow implements a Promise-like interface. You can add
callback functions `on_done`, `on_error`, `on_always` to hook different events. In the example below, our Flow passes
the message then prints the result when successful. If something goes wrong, it beeps. Finally, the result is written
to `output.txt`.

```python
from jina import Document, Flow


def beep(*args):
    # make a beep sound
    import os
    os.system('echo -n "\a";')


with Flow().add() as f, open('output.txt', 'w') as fp:
    f.post('/',
           Document(),
           on_done=print,
           on_error=beep,
           on_always=lambda x: fp.write(x.json()))
```

#### Send Parameters

To send parameters to the Executor, use

```python
from jina import Document, Executor, Flow, requests


class MyExecutor(Executor):

    @requests
    def foo(self, parameters, **kwargs):
        print(parameters['hello'])


f = Flow().add(uses=MyExecutor)

with f:
    f.post('/', Document(), parameters={'hello': 'world'})
```

Note that you can send a parameters-only data request via:

```python
with f:
    f.post('/', parameters={'hello': 'world'})
```

This is useful to control `Executor` objects in the runtime.

### Asynchronous Flow

`AsyncFlow` is an "async version" of the `Flow` class.

The quote mark represents the explicit async when using `AsyncFlow`.

While synchronous from outside, `Flow` also runs asynchronously under the hood: it manages the eventloop(s) for
scheduling the jobs. If the user wants more control over the eventloop, then `AsyncFlow` can be used.

To create an `AsyncFlow`, simply

```python
from jina import AsyncFlow

f = AsyncFlow()
```

There is also a sugary syntax `Flow(asyncio=True)` for initiating an `AsyncFlow` object.

```python
from jina import Flow

f = Flow(asyncio=True)
```

Unlike `Flow`, `AsyncFlow` accepts input and output functions
as [async generators](https://www.python.org/dev/peps/pep-0525/). This is useful when your data sources involve other
asynchronous libraries (e.g. motor for MongoDB):

```python
import asyncio

from jina import AsyncFlow, Document


async def async_inputs():
    for _ in range(10):
        yield Document()
        await asyncio.sleep(0.1)


with AsyncFlow().add() as f:
    async for resp in f.post('/', async_inputs):
        print(resp)
```

`AsyncFlow` is particularly useful when Jina and another heavy-lifting job are running concurrently:

```python
import time
import asyncio

from jina import AsyncFlow, Executor, requests


class HeavyWork(Executor):

    @requests
    def foo(self, **kwargs):
        time.sleep(5)


async def run_async_flow_5s():
    with AsyncFlow().add(uses=HeavyWork) as f:
        async for resp in f.post('/'):
            print(resp)


async def heavylifting():  # total roundtrip takes ~5s
    print('heavylifting other io-bound jobs, e.g. download, upload, file io')
    await asyncio.sleep(5)
    print('heavylifting done after 5s')


async def concurrent_main():  # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
    await asyncio.gather(run_async_flow_5s(), heavylifting())


if __name__ == '__main__':
    asyncio.run(concurrent_main())
```

`AsyncFlow` is very useful when using Jina inside a Jupyter Notebook, where it can run out-of-the-box.


## Flow as a Service

A Flow _is_ a service. Though implicit, you are already using it as a service.

When you start a `Flow` and call `.post()` inside the context, a `jina.Client` object is started and used for communication.

<img src="https://github.com/jina-ai/jina/blob/master/.github/2.0/implict-vs-explicit-service.svg?raw=true"/>

Many times we need to use Flow & Client in a more explicit way, often due to one of the following reasons:
- `Flow` and `Client` are on different machines: one on GPU, one on CPU
- `Flow` and `Client` have different lifetime: one lives longer, one lives shorter.
- Multiple `Client` want to access one `Flow`;
- One `Client` want to interleave its access to multiple `Flow`. 

So here is how:

### Python Client with gRPC Request

On the server-side, create an empty Flow and use `.block` to prevent the process exiting.

```python
from jina import Flow

with Flow(port_expose=12345) as f:
  f.block()
```

```text
        gateway@27251[I]:starting jina.peapods.runtimes.asyncio.grpc.GRPCRuntime...
        gateway@27251[I]:input tcp://0.0.0.0:58106 (PULL_CONNECT) output tcp://0.0.0.0:58106 (PUSH_BIND) control over ipc:///var/folders/89/wxpq1yjn44g26_kcbylqkcb40000gn/T/tmp0ygqijgx (PAIR_BIND)
        gateway@27251[S]:GRPCRuntime is listening at: 0.0.0.0:12345
        gateway@27247[S]:ready and listening
           Flow@27247[I]:1 Pods (i.e. 1 Peas) are running in this Flow
           Flow@27247[S]:🎉 Flow is ready to use, accepting gRPC request
           Flow@27247[I]:
	🖥️ Local access:	tcp://0.0.0.0:12345
	🔒 Private network:	tcp://192.168.1.14:12345
```

Note that the host address is `192.168.1.14` and `port_expose` is `12345`.

While keep this server open, let's create a client on a different machine:

```python
from jina import Client

c = Client(host='192.168.1.14', port_expose=12345)

c.post('/')
```

```text
         GRPCClient@27219[S]:connected to the gateway at 192.168.1.14:12345!
  |█                   | 📃    100 ⏱️ 0.0s 🐎 26690.1/s      1   requests takes 0 seconds (0.00s)
	✅ done in ⏱ 0 seconds 🐎 24854.8/s
```


### Switch REST & gRPC Request

By default all `.post()` communications are via `gRPC` interface.

To enable a Flow to receive from an HTTP request, you can add `restful=True` in the Flow constructor.

```python
from jina import Flow

f = Flow(restful=True).add(...)

with f:
    f.block()
```

You can switch to REST interface also via `.use_rest_gateway()`. Switching back to gRPC can be done
via `.use_grpc_gateway()`.

Note, unlike 1.x these two functions can be used **inside the `with` context after the Flow has started**:

```python
from jina import Flow, Document

f = Flow()

with f:
    f.post('/index', Document())  # indexing data

    f.use_rest_gateway()  # switch to REST to accept HTTP request
    f.block()
```

You will see console prints logs as follows:

```console
           JINA@4262[I]:input tcp://0.0.0.0:53894 (PULL_CONNECT) output tcp://0.0.0.0:53894 (PUSH_BIND) control over ipc:///var/folders/89/wxpq1yjn44g26_kcbylqkcb40000gn/T/tmp4e9u2pdn (PAIR_BIND)
           JINA@4262[I]:
    Jina REST interface
    💬 Swagger UI:	http://localhost:53895/docs
    📚 Redoc     :	http://localhost:53895/redoc
        
           JINA@4262[S]:ready and listening
        gateway@4262[S]:RESTRuntime is listening at: 0.0.0.0:53895
        gateway@4251[S]:ready and listening
```

You can navigate to the Swagger docs UI via `http://localhost:53895/docs`:

<img src="https://github.com/jina-ai/jina/blob/master/.github/2.0/swagger-ui.png?raw=true"/>

### `curl` with HTTP Request

Now you can send data request via `curl`/Postman:

```console
$ curl --request POST -d '{"data": [{"text": "hello world"}]}' -H 'Content-Type: application/json' http://localhost:53895/post/index

{
  "request_id": "1f52dae0-93a5-47b5-9fa0-522a75301d99",
  "data": {
    "docs": [
      {
        "id": "28287a66-b86a-11eb-99c2-1e008a366d49",
        "tags": {},
        "text": "hello world",
        "content_hash": "",
        "granularity": 0,
        "adjacency": 0,
        "parent_id": "",
        "chunks": [],
        "weight": 0.0,
        "siblings": 0,
        "matches": [],
        "mime_type": "",
        "location": [],
        "offset": 0,
        "modality": "",
        "evaluations": []
      }
    ],
    "groundtruths": []
  },
  "header": {
    "exec_endpoint": "index",
    "target_peapod": "",
    "no_propagate": false
  },
  "routes": [
    {
      "pod": "gateway",
      "pod_id": "5e4211d0-3916-4f33-8b9e-eec54be8ed9a",
      "start_time": "2021-05-19T06:19:24.472050Z",
      "end_time": "2021-05-19T06:19:24.473895Z"
    },
    {
      "pod": "gateway",
      "pod_id": "83a7ad34-1042-4b5d-b065-3692e2fc691b",
      "start_time": "2021-05-19T06:19:24.473831Z"
    }
  ],
  "status": {
    "code": "SUCCESS",
    "description": ""
  }
}
```

When use `curl`, make sure to pass the `-N/--no-buffer` flag.

### Python Client with REST Request

In some case when `restful=True`, you may still need a Python client to query the server for debugging. You can use `Client` with an additional parameter `restful` in this case.

```python
from jina import Client

c = Client(host='192.168.1.14', port_expose=12345, restful=True)
c.post('/')
```

```text
         WebSocketClient@27622[S]:Connected to the gateway at 192.168.1.14:12345
  |█                   | 📃    100 ⏱️ 0.0s 🐎 19476.6/s      1   requests takes 0 seconds (0.00s)
	✅ done in ⏱ 0 seconds 🐎 18578.9/s
```


### Extend FastAPI interface

If you want to add more customized routes, configs, options to FastAPI's REST interface, you can simply override `jina.helper.extend_rest_interface` function as follows:

```python
import jina.helper
from jina import Flow


def extend_rest_function(app):

    @app.get('/hello', tags=['My Extended APIs'])
    async def foo():
        return 'hello'

    return app


jina.helper.extend_rest_interface = extend_rest_function
f = Flow(restful=True)

with f:
    f.block()
```

And you will see `/hello` is now available:

![img.png](../swagger-extend.png)

---

## Remarks

### Joining/Merging

Combining `docs` from multiple requests is already done by the `ZEDRuntime` before feeding them to the Executor's function.
Hence, simple joining is just returning this `docs`. Complicated joining should be implemented at `Document`
/`DocumentArray`

```python
from jina import Executor, requests, Flow, Document


class C(Executor):

    @requests
    def foo(self, docs, **kwargs):
        # 6 docs
        return docs


class B(Executor):

    @requests
    def foo(self, docs, **kwargs):
        # 3 docs
        for idx, d in enumerate(docs):
            d.text = f'hello {idx}'


class A(Executor):

    @requests
    def A(self, docs, **kwargs):
        # 3 docs
        for idx, d in enumerate(docs):
            d.text = f'world {idx}'


f = Flow().add(uses=A).add(uses=B, needs='gateway').add(uses=C, needs=['pod0', 'pod1'])

with f:
    f.post(on='/some_endpoint',
           inputs=[Document() for _ in range(3)],
           on_done=print)
```

You can also modify the Documents while merging, which was not feasible to do in 1.x:

```python
class C(Executor):

    @requests
    def foo(self, docs, **kwargs):
        # 6 docs
        for d in docs:
            d.text += '!!!'
        return docs
```
