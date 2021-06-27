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
    - [Fine-grained Control on Request](#fine-grained-control-on-request)
    - [Get All Responses](#get-all-responses)
  - [Asynchronous Flow](#asynchronous-flow)
- [Remarks](#remarks)
  - [Joining/Merging](#joiningmerging)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum working example

### Pure Python: All-in-one Style 

```python
from jina import Flow, Document, Executor, requests


class MyExecutor(Executor):

    @requests(on='/bar')
    def foo(self, docs, **kwargs):
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

    @requests(on='/bar')
    def foo(self, docs, **kwargs):
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
|Control| `.block()` |

### Create a Flow

An empty Flow can be created via:

```python
from jina import Flow

f = Flow()
```

### Use a Flow

To use `f`, always open it as a context manager, just like you open a file. This is considered the best practice in
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
        request_size: int = 100,
        show_progress: bool = False,
        continue_on_error: bool = False,
        return_results: bool = False,
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
    :param request_size: the number of Documents per request. <=0 means all inputs in one request.
    :param show_progress: if set, client will show a progress bar on receiving every request.
    :param continue_on_error: if set, a Request that causes callback error will be logged only without blocking the further requests.
    :param return_results: if set, the results of all Requests will be returned as a list. This is useful when one wants process Responses in bulk instead of using callback.
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

Once a request is returned, callback functions are fired. Jina Flow implements a Promise-like interface. You can add
callback functions `on_done`, `on_error`, `on_always` to hook different events. 

In Jina, callback function's first argument is a `jina.types.request.Response` object. Hence, you can annotate the callback function via:

```python
from jina.types.request import Response

def my_callback(rep: Response):
    ...
```

`Response` object has many attributes, probably the most popular one is `Response.docs`, where you can access all `Document` as an `DocumentArray`.

In the example below, our Flow passes
the message then prints the result when successful. If something goes wrong, it beeps. Finally, the result is written
to `output.txt`.

```python
from jina import Document, Flow


def beep(*args):
    # make a beep sound
    import sys
    sys.stdout.write('\a')


with Flow().add() as f, open('output.txt', 'w') as fp:
    f.post('/',
           Document(),
           on_done=print,
           on_error=beep,
           on_always=lambda x: x.docs.save(fp))
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


#### Fine-grained Control on Request

##### Size of the Request

You can control how many `Documents` in each request by `request_size`. Say your `inputs` has length of 100, whereas you `request_size` is set to `10`. Then `f.post` will send ten requests and return 10 responses:

```python
from jina import Flow, Document

f = Flow()

with f:
    f.post('/', (Document() for _ in range(100)), request_size=10)
```

```console
        gateway@8869[I]:input tcp://0.0.0.0:53021 (ROUTER_BIND) output None (DEALER_CONNECT) control over ipc:///var/folders/89/wxpq1yjn44g26_kcbylqkcb40000gn/T/tmpdryull18 (PAIR_BIND)
        gateway@8869[S]:GRPCRuntime is listening at: 0.0.0.0:53023
        gateway@8865[S]:ready and listening
           Flow@8865[I]:1 Pods (i.e. 1 Peas) are running in this Flow
           Flow@8865[S]:🎉 Flow is ready to use!
           Flow@8865[I]:
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:53023
	🔒 Private network:	192.168.31.159:53023
     GRPCClient@8865[S]:connected to the gateway at 0.0.0.0:53023!

        ...
        
        gateway@8869[I]:#sent: 10 #recv: 10 sent_size: 10.3 KB recv_size: 9.7 KB
        gateway@8865[S]:terminated
           Flow@8865[S]:flow is closed and all resources are released, current build level is 0
```

To see that more clearly, you can turn on the progress-bar by `show_progress`.

```python
with f:
    f.post('/', (Document() for _ in range(100)), request_size=10, show_progress=True)
```

```console
     GRPCClient@8903[S]:connected to the gateway at 0.0.0.0:53061!
  |█                   | ⏳      0 ⏱️ 0.0s 🐎   0 QPS ...	        gateway@8907[I]:prefetching 50 requests...
        gateway@8907[W]:if this takes too long, you may want to take smaller "--prefetch" or ask client to reduce `request_size`
        gateway@8907[I]:prefetching 50 requests takes 0 seconds (0.01s)
  |██████████          | ⏳     10 ⏱️ 0.0s 🐎 769 QPS takes 0 seconds (0.01s)
	✅ done in ⏱ 0 seconds 🐎 757 QPS
        gateway@8907[I]:#sent: 10 #recv: 10 sent_size: 10.3 KB recv_size: 9.7 KB
        gateway@8903[S]:terminated
           Flow@8903[S]:flow is closed and all resources are released, current build level is 0

```

#### Get All Responses

In some scenarios (e.g. testing), you may want to get the all responses in bulk and then process them; instead of processing responses on the fly. To do that, you can turn on `return_results`:

```python
from jina import Flow, Document

f = Flow()

with f:
    all_responses = f.post('/', (Document() for _ in range(100)), request_size=10, return_results=True)
    print(all_responses)
```

```console
        gateway@9003[I]:input tcp://0.0.0.0:53174 (ROUTER_BIND) output None (DEALER_CONNECT) control over ipc:///var/folders/89/wxpq1yjn44g26_kcbylqkcb40000gn/T/tmpgu5yqxyw (PAIR_BIND)
        gateway@9003[S]:GRPCRuntime is listening at: 0.0.0.0:53176
        gateway@9000[S]:ready and listening
           Flow@9000[I]:1 Pods (i.e. 1 Peas) are running in this Flow
           Flow@9000[S]:🎉 Flow is ready to use!
           Flow@9000[I]:
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:53176
	🔒 Private network:	192.168.31.159:53176
     GRPCClient@9000[S]:connected to the gateway at 0.0.0.0:53176!
        gateway@9003[I]:prefetching 50 requests...
        gateway@9003[W]:if this takes too long, you may want to take smaller "--prefetch" or ask client to reduce `request_size`
        gateway@9003[I]:prefetching 50 requests takes 0 seconds (0.01s)
[<jina.types.request.Response request_id=116880a6-acd7-474a-8ec6-71bab47041cd data={'docs': [{'id': 'e42c22dc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2552-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c26e2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2836-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c298a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2ad4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2c1e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2d5e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2ea8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2ff2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.896226Z', 'end_time': '2021-06-23T06:04:37.897433Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.897424Z'}] status={} at 5673238672>,
 <jina.types.request.Response request_id=37040d37-6835-443e-8741-b2f762ae95cc data={'docs': [{'id': 'e42c806a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c8a10-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c8e70-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c9276-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c9668-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ca748-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ca996-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42caaf4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cb40e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cb594-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.898454Z', 'end_time': '2021-06-23T06:04:37.899392Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.899384Z'}] status={} at 5678885008>,
 <jina.types.request.Response request_id=54eddb8b-8691-446f-98bc-1d492f5bedb0 data={'docs': [{'id': 'e42cfc16-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cfdb0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cff04-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d0044-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d017a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d02ba-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d03fa-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d053a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d067a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d07b0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.900145Z', 'end_time': '2021-06-23T06:04:37.901004Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.900997Z'}] status={} at 5721399952>,
 <jina.types.request.Response request_id=653e1721-5371-42fb-98e8-714293a0b5bc data={'docs': [{'id': 'e42bc468-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd228-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd462-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd5fc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd76e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd8cc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bda20-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bdb7e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bdcd2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bde1c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.891429Z', 'end_time': '2021-06-23T06:04:37.895875Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.895849Z'}] status={} at 5724839696>,
 <jina.types.request.Response request_id=5e8dddcc-0215-45cb-8d48-289c0e6f60ca data={'docs': [{'id': 'e42c086a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c0be4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c0d88-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c0f04-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c1062-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c11c0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c133c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c147c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c15c6-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c1710-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.894530Z', 'end_time': '2021-06-23T06:04:37.896864Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.896851Z'}] status={} at 5724838800>,
 <jina.types.request.Response request_id=d207de83-52c6-4287-8504-d6ab08816987 data={'docs': [{'id': 'e42c5306-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c55ea-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c57a2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5946-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5ab8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5c20-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5d7e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5edc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c603a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c618e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.897747Z', 'end_time': '2021-06-23T06:04:37.898746Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.898738Z'}] status={} at 5724838864>,
 <jina.types.request.Response request_id=590ae511-b5ad-4bd7-9ed1-baba2c63aadf data={'docs': [{'id': 'e42ce596-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ce730-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ce884-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ce9d8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ceb18-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cec76-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cedf2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cef28-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cf068-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cf1a8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.899588Z', 'end_time': '2021-06-23T06:04:37.900536Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.900527Z'}] status={} at 4468253072>,
 <jina.types.request.Response request_id=4771806e-6c33-4a75-a519-85916a949ea2 data={'docs': [{'id': 'e42c3a06-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c3bf0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c3d6c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c3ede-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c4050-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c41ae-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c430c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c446a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c45c8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c473a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.897122Z', 'end_time': '2021-06-23T06:04:37.898220Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.898208Z'}] status={} at 5724837648>,
 <jina.types.request.Response request_id=76d92a47-7ce5-4a86-aab2-c3ced227d8e4 data={'docs': [{'id': 'e42cce62-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd074-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd1c8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd312-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd452-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd592-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd6d2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd81c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd95c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cda9c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.899022Z', 'end_time': '2021-06-23T06:04:37.899859Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.899852Z'}] status={} at 5724837264>,
 <jina.types.request.Response request_id=c741e3dd-c57e-4deb-b074-99cd65037e05 data={'docs': [{'id': 'e42d123c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d143a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d15ac-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1700-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d184a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d198a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1ad4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1c14-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1d54-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1e9e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.900727Z', 'end_time': '2021-06-23T06:04:37.902004Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.901984Z'}] status={} at 5724837200>]
        gateway@9003[I]:#sent: 10 #recv: 10 sent_size: 10.3 KB recv_size: 9.7 KB
        gateway@9000[S]:terminated
           Flow@9000[S]:flow is closed and all resources are released, current build level is 0

```

Note, turning on `return_results` breaks the streaming of the system. If you are sending 1000 requests, then `return_results=True` means you will get nothing until the 1000th response returns. Moreover, if each response takes 10MB memory, it means you will consume upto 10GB memory! On contrary, with callback and `return_results=False`, your memory usage will stay constant at 10MB. 



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
