(flow-cookbook)=
# Flow

{class}`~jina.Flow` orchestrates Executors into a processing pipeline to build a neural search application.
Documents "flow" through the created pipeline and are processed by Executors.


The most important methods of the `Flow` object are the following:

| Method         | Description                                                                                          |
|----------------|------------------------------------------------------------------------------------------------------|
|  `.add()` | Add an Executor to the `Flow`                                                                        |
| `with` context manager       | You can use the `Flow` as a context manager. It will automatically start and close your `Flow` then. |
| `.plot()` | Visualizes the flow. Helpful for building complex pipelines.                                         |
| `.post()`   | Sends requests to the API of the `Flow`.                                                             |
| `.block()`        | Blocks execution until the program is terminated.                                                    |



## Minimum working example

````{tab} Pythonic style


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

- <a href="https://docarray.jina.ai/>Document</a> is the basic data type in Jina;
- {ref}`Executor <executor>` is how Jina processes Documents;
- {ref}`Flow <flow>` is how Jina streamlines and scales Executors.
````


```{toctree}
:hidden:

create-flow
flow-api
docker
k8s
remarks
```
