(flow-cookbook)=
# Flow

A {class}`~jina.Flow` orchestrates {class}`~jina.Executor`s into a processing pipeline to accomplish a task.
Documents "flow" through the pipeline and are processed by Executors.

You can think of Flow as an interface to configure and launch your {ref}`microservice architecture <architecture-overview>`,
while the heavy lifting is done by the {ref}`services <executor-cookbook>` themselves.
In particular, each Flow also launches a {ref}`Gateway <gateway>` service, which can expose all other services through an API that you define.

The most important methods of the `Flow` object are the following:

| Method                                                       | Description                                                                                                                                                                                                                                                                          |
|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| {meth}`~jina.Flow.add`                                       | Adds an Executor to the Flow                                                                                                                                                                                                                                                         |
| {meth}`~jina.Flow.start()`                                   | Starts the Flow. This will start all its Executors and check if they are ready to be used.                                                                                                                                                                                           |
| {meth}`~jina.Flow.close()`                                   | Stops and closes the Flow. This will stop and shutdown all its Executors.                                                                                                                                                                                                            |
| `with` context manager                                       | Uses the Flow as a context manager. It will automatically start and stop your Flow.                                                                                                                                                                                                   |                                                                |
| {meth}`~jina.Flow.plot()`                                    | Visualizes the Flow. Helpful for building complex pipelines.                                                                                                                                                                                                                         |
| {meth}`~jina.clients.mixin.PostMixin.post()`                 | Sends requests to the Flow API.                                                                                                                                                                                                                                                      |
| {meth}`~jina.Flow.block()`                                   | Blocks execution until the program is terminated. This is useful to keep the Flow alive so it can be used from other places (clients, etc).                                                                                                                                          |
| {meth}`~jina.Flow.to_docker_compose_yaml()`                  | Generates a Docker-Compose file listing all Executors as services.                                                                                                                                                                                                                                                |
| {meth}`~jina.Flow.to_kubernetes_yaml()`                      | Generates Kubernetes configuration files in `<output_directory>`. Based on your local Jina version, Executor Hub may rebuild the Docker image during the YAML generation process. If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.                                                                                                                                   |
| {meth}`~jina.clients.mixin.HealthCheckMixin.is_flow_ready()` | Check if the Flow is ready to process requests. Returns a boolean indicating the readiness.                                                                                                                                                                                                                                                                                                                                 |

## Why should you use a Flow?

Once you've learned DocumentArray and Executor, you can split a big task into small independent modules and services.
But you need to chain them together to bring real value and build and serve an application. Flows enable you to do exactly this.

- Flows connect microservices (Executors) to build a service with proper client/server style interface over HTTP, gRPC, or WebSockets.

- Flows let you scale these Executors independently to match your requirements.

- Flows let you easily use other cloud-native orchestrators, such as Kubernetes, to manage your service.

## Minimum working example

````{tab} Pythonic style


```python
from jina import Flow, Executor, requests, Document


class MyExecutor(Executor):
    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


f = Flow().add(name='myexec1', uses=MyExecutor)

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```


````

````{tab} Flow-as-a-Service style

Server:

```python
from jina import Flow, Executor, requests


class MyExecutor(Executor):
    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


f = Flow(port=12345).add(name='myexec1', uses=MyExecutor)

with f:
    f.block()
```

Client:

```python
from jina import Client, Document

c = Client(port=12345)
c.post(on='/bar', inputs=Document(), on_done=print)
```

````

````{tab} Load from YAML

`my.yml`:
```yaml
jtype: Flow
executors:
  - name: myexec1
    uses: FooExecutor
    py_modules: exec.py
```

`exec.py`:
```python
from jina import Executor, requests, Document, DocumentArray


class FooExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))
```

```python
from jina import Flow, Document

f = Flow.load_config('my.yml')

with f:
    try:
        f.post(on='/bar', inputs=Document(), on_done=print)
    except Exception as ex:
        # handle exception
        pass
```

````

```{caution}
The statement `with f:` starts the Flow, and exiting the indented with block stops the Flow, including all Executors defined in it.
Exceptions raised inside the `with f:` block will close the Flow context manager. If you don't want this, use a `try...except` block to surround the statements that could potentially raise an exception.
```

## Adding Executors

A {class}`~jina.Flow` orchestrates its {class}`~jina.Executor`s as a graph and sends requests to all Executors in the order specified by {meth}`~jina.Flow.add` or listed in {ref}`a YAML file<flow-yaml-spec>`. 

When you start a Flow, Executors always run in **separate processes**. Multiple Executors run in **different processes**. Multiprocessing is the lowest level of separation when you run a Flow locally. When running a Flow on Kubernetes, Docker Swarm, {ref}`jcloud`, different Executors run in different containers, pods or instances.   

## Executors in Flows

Executors can be added into a Flow with {meth}`~jina.Flow.add`.  

```python
from jina import Flow

f = Flow().add()
```

This adds an "empty" Executor called {class}`~jina.serve.executors.BaseExecutor` to the Flow. This Executor (without any parameters) performs no actions.

```{figure} no-op-flow.svg
:scale: 70%
```

To more easily identify an Executor, you can change its name by passing the `name` parameter:

```python
from jina import Flow

f = Flow().add(name='myVeryFirstExecutor').add(name='secondIsBest')
```


```{figure} named-flow.svg
:scale: 70%
```

You can also define the above Flow in YAML:

```yaml
jtype: Flow
executors:
  - name: myVeryFirstExecutor
  - name: secondIsBest
```

Save it as `flow.yml` and run it: 

```bash
jina flow --uses flow.yml
```

More Flow YAML specifications can be found in {ref}`Flow YAML Specification<flow-yaml-spec>`.

## Define topologies over Executors

{class}`~jina.Flow`s are not restricted to sequential execution. Internally they are modeled as graphs, so they can represent any complex, non-cyclic topology.

A typical use case for such a Flow is a topology with a common pre-processing part, but different indexers separating embeddings and data.

To define a custom topology you can use the `needs` keyword when adding an {class}`~jina.Executor`. By default, a Flow assumes that every Executor needs the previously added Executor.

```python
from jina import Executor, Flow, requests, Document, DocumentArray


class FooExecutor(Executor):
    @requests
    async def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'foo was here and got {len(docs)} document'))


class BarExecutor(Executor):
    @requests
    async def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'bar was here and got {len(docs)} document'))


class BazExecutor(Executor):
    @requests
    async def baz(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'baz was here and got {len(docs)} document'))


f = (
    Flow()
    .add(uses=FooExecutor, name='fooExecutor')
    .add(uses=BarExecutor, name='barExecutor', needs='fooExecutor')
    .add(uses=BazExecutor, name='bazExecutor', needs='fooExecutor')
    .add(needs=['barExecutor', 'bazExecutor'])
)
```

```{figure} needs-flow.svg
:width: 70%
:align: center
Complex Flow where one Executor requires two Executors to process Documents beforehand
```

When sending message to this Flow,

```python
with f:
    print(f.post('/').texts)
```

This gives the output:

```text
['foo was here and got 0 document', 'bar was here and got 1 document', 'baz was here and got 1 document']
```

Both `BarExecutor` and `BazExecutor` only received a single `Document` from `FooExecutor` because they are run in parallel. The last Executor `executor3` receives both DocumentArrays and merges them automatically.
This automated merging can be disabled with `no_reduce=True`. This is useful for providing custom merge logic in a separate Executor. In this case the last `.add()` call would look like `.add(needs=['barExecutor', 'bazExecutor'], uses=CustomMergeExecutor, no_reduce=True)`. This feature requires Jina >= 3.0.2.

## How Executors process DocumentArrays in a Flow

Let's understand how Executors process DocumentArray's inside a Flow, and how changes are chained and applied, affecting downstream Executors in the Flow.

```python 
from jina import Executor, requests, Flow, DocumentArray, Document


class PrintDocuments(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(f' PrintExecutor: received document with text: "{doc.text}"')


class ProcessDocuments(Executor):
    @requests(on='/change_in_place')
    def in_place(self, docs, **kwargs):
        # This Executor only works on `docs` and doesn't consider any other arguments
        for doc in docs:
            print(f' ProcessDocuments: received document with text "{doc.text}"')
            doc.text = 'I changed the executor in place'

    @requests(on='/return_different_docarray')
    def ret_docs(self, docs, **kwargs):
        # This executor only works on `docs` and doesn't consider any other arguments
        ret = DocumentArray()
        for doc in docs:
            print(f' ProcessDocuments: received document with text: "{doc.text}"')
            ret.append(Document(text='I returned a different Document'))
        return ret


f = Flow().add(uses=ProcessDocuments).add(uses=PrintDocuments)

with f:
    f.post(on='/change_in_place', inputs=DocumentArray(Document(text='request1')))
    f.post(
        on='/return_different_docarray', inputs=DocumentArray(Document(text='request2'))
    )
```


```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:58746  │
│  🔒     Private     192.168.1.187:58746  │
│  🌍      Public    212.231.186.65:58746  │
╰──────────────────────────────────────────╯

 ProcessDocuments: received document with text "request1"
 PrintExecutor: received document with text: "I changed the executor in place"
 ProcessDocuments: received document with text: "request2"
 PrintExecutor: received document with text: "I returned a different Document"
```

