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

## gRPC Client and Threading
Since multi-threading is not supported for asyncio gRPC clients, using the gRPC Client in different threads is not 
supported. In fact, any usage outside the main thread will result in a `GRPCClientThreadingError`:

```{code-block} python
---
emphasize-lines: 7, 12
---
from threading import Thread
from jina import Flow

def start_f():
    f = Flow(protocol='grpc').add(uses=DummyExecutor, replicas=3, polling='ALL')
    with f:
        f.post('/')


for _ in range(4):
    # multi-threaded use of the gRPC Client
    t = Thread(target=start_f)
    t.start()
```

```text
jina.excepts.GRPCClientThreadingError: Using GRPCClient outside the main thread is not allowed. Please opt for 
multi-processing instead.
```


````{admonition} Note
:class: note
Using `Flow.post` on a Flow that uses the gRPC protocol will simply call the gRPC Client. Therefore, this method 
shouldn't be multi-threaded if the Flow uses gRPC. 
````

````{admonition} Note
:class: note
By default, the gRPC protocol is used for the Flow if the `protocol` parameter is not specified.
````
