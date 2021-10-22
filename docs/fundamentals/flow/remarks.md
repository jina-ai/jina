# Remarks


## Joining/Merging

Combining `docs` from multiple requests is already done by the `ZEDRuntime` before feeding them to the Executor's
function. Hence, simple joining is just returning this `docs`. Complicated joining should be implemented at `Document`
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


f = Flow().add(uses=A).add(uses=B, needs='gateway').add(uses=C, needs=['executor0', 'executor1'])

with f:
    f.post(on='/some_endpoint',
           inputs=[Document() for _ in range(3)],
           on_done=print)
```

You can also modify the Documents while merging:

```python
class C(Executor):

    @requests
    def foo(self, docs, **kwargs):
        # 6 docs
        for d in docs:
            d.text += '!!!'
        return docs
```

## Multiple Flows and Parallelism
Creating multiple flows through process-based parallelism is supported for all protocols of the Flow client.
However, using thread-based parallelism to create multiple Flows is not supported for the gRPC protocol. This 
limitation comes from the fact that multi-threading is not supported for asyncio gRPC clients. In general, 
multi-threaded use of the Flow gRPC Client is not supported and any usage outside the main thread will result in a 
`GRPCClientThreadingError`:

````{tab} ❌ GRPC Flows with threads
```{code-block} python
from threading import Thread
from jina import Flow

def start_f():
    f = Flow(protocol='grpc').add(uses=DummyExecutor, parallel=3, polling='ALL')
    with f:
        f.post('/')


for _ in range(4):
    t = Thread(target=start_f)
    t.start()
```

```text
jina.excepts.GRPCClientThreadingError: Using GRPCCLient outside the main thread is not allowed. Please opt for 
multi-processing instead.
```
````

````{tab} ✅ GRPC Flows with processes
```{code-block} python
from multiprocessing import Process
from jina import Flow

def start_f():
    f = Flow(protocol='grpc').add(uses=DummyExecutor, parallel=3, polling='ALL')
    with f:
        f.post('/')


for _ in range(4):
    t = Process(target=start_f)
    t.start()
```
````

````{tab} ✅ HTTP Flows with threads
```{code-block} python
from threading import Thread
from jina import Flow

def start_f():
    f = Flow(protocol='http').add(uses=DummyExecutor, parallel=3, polling='ALL')
    with f:
        f.post('/')


for _ in range(4):
    t = Thread(target=start_f)
    t.start()
```
````

````{admonition} Note
:class: note
By default, the gRPC protocl is used for the Flow if the `protocol` parameter is not specified.
````