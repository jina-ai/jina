Document, Executor, Flow are three fundamental concepts in Jina.

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
    - [Pure Python](#pure-python)
    - [With YAML](#with-yaml)
- [Flow API](#flow-api)
    - [Create a Flow](#create-a-flow)
    - [Add Executor to a Flow](#add-executor-to-a-flow)
    - [Create Inter & Intra Parallelism via `needs`](#create-inter--intra-parallelism-via-needs)
    - [Decentralized Flow](#decentralized-flow)
    - [Send Data to Flow](#send-data-to-flow)
        - [`post` method](#post-method)
    - [Fetch Result from Flow](#fetch-result-from-flow)
    - [Asynchronous Flow](#asynchronous-flow)
    - [REST Interface](#rest-interface)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum working example

### Pure Python

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

In Jina, Flow is how Jina streamlines and scales Executors. A `Flow` object has the following common methods:

| |  |
|---|---|
|Construct Flow| `.add()`, `.needs()` |
|Run Flow| `with` context manager |
|Visualize Flow| `.plot()` |
|Send Request| `.post()`|
|Control Gateway| `.use_grpc_gateway()`, `.use_rest_gateway()`

### Create a Flow

An empty Flow can be created via:

```python
from jina import Flow

f = Flow()
```

To use `f`, always open it as a content manager. Just like you open a file. This is considered as the best practice in Jina:

```python
with f:
    ...
```

Note that, Flow follows a lazy construction pattern: it won't be actually running until you use `with` to open it.

### Visualize a Flow

```python
from jina import Flow

f = Flow().add().plot('f.svg')
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/2.0/empty-flow.svg?raw=true"/>

In Jupyter Lab/Notebook, `Flow` object is rendered automatically, there is no need to do call `plot()`.

### Add `Executor` to a Flow

`.add()` is the core method to add executor to a `Flow` object. Each `add` creates a new Executor, and these Executors
can be run as a local thread/process, a remote process, inside a Docker container, or even inside a remote Docker
container.

`.add()` accepts the following common arguments:

| |  |
|---|---|
|Define Executor| `uses`|
|Define Dependency | `needs` |
|Parallelization | `parallel`, `polling` |

For a full list of arguments, please check `jina executor --help`.

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
        'with': {'bar': 123}}
)
```

Chaining `.add()`s creates a sequential Flow.

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

`.needs()` is a syntax sugar and roughly equal to

```python
.add(needs=['p1', 'p2', 'p3'])
```

`.needs_all()` is a syntax sugar and roughly equal to

```python
.add(needs=[all_orphan_executors_so_far])
```

"Orphan" executors have no connected executors to their outputs. The above code snippet can be also written as:

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

To change that behavior, you can add `polling` argument to `.add()`, e.g. `.add(parallel=3, polling='ALL')`. Specifically,

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

A Flow does not have to be local-only. You can put any Executor to remote(s). In the example below, with the `host`
keyword `gpu-exec`, is put to a remote machine for parallelization, whereas other Executors stay local. Extra file
dependencies that need to be uploaded are specified via the `upload_files` keyword.

<table>
    <tr>
    <td>123.456.78.9</td>
    <td>

```bash
# have docker installed
docker run --name=jinad --network=host -v /var/run/docker.sock:/var/run/docker.sock jinaai/jina:latest-daemon --port-expose 8000
 to stop it
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

### Send Data to Flow

#### `post` method

`post` is the core method. All 1.x methods, e.g. `index`, `search`, `update`, `delete` are just sugary syntax of `post`
by specifying `on='/index'`, `on='/search'`, etc.

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

Comparing to 1.x Client/Flow API, the three new arguments are:

- `on`: endpoint, as explained above
- `parameters`: the kwargs that will be sent to the executor, as explained above
- `target_peapod`: a regex string represent the certain peas/pods request targeted

### Fetch Result from Flow

Once a request is done, callback functions are fired. Jina Flow implements a Promise-like interface: You can add
callback functions `on_done`, `on_error`, `on_always` to hook different events. In the example below, our Flow passes
the message then prints the result when successful. If something goes wrong, it beeps. Finally, the result is written
to `output.txt`.

```python
def beep(*args):
    # make a beep sound
    import os
    os.system('echo -n "\a";')


with Flow().add() as f, open('output.txt', 'w') as fp:
    f.index(numpy.random.random([4, 5, 2]),
            on_done=print, on_error=beep, on_always=lambda x: fp.write(x.json()))
```

### Asynchronous Flow

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-inter-intra-parallelism.ipynb)

While synchronous from outside, Jina runs asynchronously under the hood: it manages the eventloop(s) for scheduling the
jobs. If the user wants more control over the eventloop, then `AsyncFlow` can be used.

Unlike `Flow`, the CRUD of `AsyncFlow` accepts input and output functions
as [async generators](https://www.python.org/dev/peps/pep-0525/). This is useful when your data sources involve other
asynchronous libraries (e.g. motor for MongoDB):

```python
from jina import AsyncFlow


async def input_function():
    for _ in range(10):
        yield Document()
        await asyncio.sleep(0.1)


with AsyncFlow().add() as f:
    async for resp in f.index(input_function):
        print(resp)
```

`AsyncFlow` is particularly useful when Jina and another heavy-lifting job are running concurrently:

```python
async def run_async_flow_5s():  # WaitDriver pause 5s makes total roundtrip ~5s
    with AsyncFlow().add(uses='- !WaitDriver {}') as f:
        async for resp in f.index_ndarray(numpy.random.random([5, 4])):
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

`AsyncFlow` is very useful when using Jina inside a Jupyter Notebook. where it can run out-of-the-box.

### REST Interface

In practice, the query Flow and the client (i.e. data sender) are often physically separated. Moreover, the client may
prefer to use a REST API rather than gRPC when querying. You can set `port_expose` to a public port and turn
on [REST support](https://api.jina.ai/rest/) with `restful=True`:

```python
f = Flow(port_expose=45678, restful=True)

with f:
    f.block()
```


