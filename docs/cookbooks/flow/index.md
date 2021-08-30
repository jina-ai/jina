(flow)=
# Flow
The `Flow` ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a 
dataset. Documents "flow" through the created pipeline and are processed by Executors.
`Flow` also provides synchronization mechanisms to manage dependencies between executors and their order.

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


```{toctree}
:hidden:

flow-api
remarks
```
