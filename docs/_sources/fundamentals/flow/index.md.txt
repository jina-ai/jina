(flow-cookbook)=
# Flow

A {class}`~jina.Flow` orchestrates Executors into a processing pipeline to build a neural search application.
Documents "flow" through the created pipeline and are processed by Executors.


The most important methods of the `Flow` object are the following:

| Method                             | Description                                                                                                                                  |
|------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `.add()`                           | Add an Executor to the Flow                                                                                                                |
| `.start()`                         | Starts the Flow. This will start all its Executors and check if they are ready to be used.                                                 |
| `.stop()`                          | Stops the Flow. This will stop all its Executors.                                                                                          |
| `with` context manager             | Use the Flow as a context manager. It will automatically start and stop your Flow.                                         |                                                                |
| `.plot()`                          | Visualizes the Flow. Helpful for building complex pipelines.                                                                                 |
| `.post()`                          | Sends requests to the Flow API.                                                                                                     |
| `.block()`                         | Blocks execution until the program is terminated. This is useful to keep the Flow alive so it can be used from other places (clients, etc). |
| `.to_docker_compose_yaml()`        | Generates a Docker-Compose file listing all its Executors as Services.                                                                       |
| `.to_k8s_yaml(<output_directory>)` | Generates the Kubernetes configuration files in `<output_directory>`.        

## Why should you use a Flow?

Once you have learned DocumentArray and Executor, you have been able to split your neural search application into different independent modules and services.
But you need to chain them together in order to bring real value and to build and serve an application out of it. That's exactly what Flows enable you to do.

- Flow connects the microservices (Executors) to build an service with proper client/server style interface in HTTP/gRPC/Websockets

- Flow lets you scale these Executors independently to adjust to your requirements.

- Flow allows you to easily use other cloud-native orchestrators, e.g. K8s to manage the service.

## Minimum working example

````{tab} Pythonic style


```python
from docarray import Document
from jina import Flow, Executor, requests


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
from docarray import Document
from jina import Client

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
from docarray import Document, DocumentArray

from jina import Executor, requests


class FooExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))
```

```python
from docarray import Document
from jina import Flow

f = Flow.load_config('my.yml')

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```

````

````{admonition} See Also
:class: seealso

Executor and Flow are the two fundamental concepts in Jina.

- <a href="https://docarray.jina.ai/">Document</a> is the basic data type in Jina
- {ref}`Executor <executor>` is how Jina processes Documents
- {ref}`Flow <flow>` is how Jina streamlines and scales Executors
````


```{toctree}
:hidden:

create-flow
flow-api
client
remarks
```
