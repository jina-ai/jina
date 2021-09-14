(flow-cookbook)=
# Flow

The `Flow` ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a 
dataset. Documents "flow" through the created pipeline and are processed by Executors.
`Flow` also provides synchronization mechanisms to manage dependencies between executors and their order.




A `Flow` object has the following common methods:

| Group | Description |
|---|---|
|Construct Flow| `.add()`, `.needs()` |
|Run Flow| `with` context manager |
|Visualize Flow| `.plot()` |
|Send Request| `.post()`|
|Control| `.block()` |



## Minimum working example

````{tab} All-in-one style


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


````

````{tab} Flow-as-a-Service style

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
    uses: MyExecutor
```

```python
from jina import Flow, Document

f = Flow.load_config('my.yml')

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```

````

````{admonition} See Also
:class: seealso

Document, Executor, and Flow are the three fundamental concepts in Jina.

- {doc}`Document <../document/index>` is the basic data type in Jina;
- {ref}`Executor <executor>` is how Jina processes Documents;
- {ref}`Flow <flow>` is how Jina streamlines and scales Executors.
````


```{toctree}
:hidden:

flow-api
send-recv
add-exec-to-flow
parallel
async-flow
flow-as-a-service
remarks
```
