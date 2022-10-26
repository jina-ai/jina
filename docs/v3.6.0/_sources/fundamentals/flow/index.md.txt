(flow-cookbook)=
# Flow

A {class}`~jina.Flow` orchestrates Executors into a processing pipeline to build a multi-modal/cross-modal application.
Documents "flow" through the created pipeline and are processed by Executors.

You can think of Flow as an interface to configure and launch your {ref}`microservice architecture <architecture-overview>`,
while the heavy lifting is done by the {ref}`services <executor-cookbook>` themselves.
In particular, each Flow also launches a *Gateway* service, which can expose all other services through an API that you define.


The most important methods of the `Flow` object are the following:

| Method                             | Description                                                                                                                                  |
|------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `.add()`                           | Add an Executor to the Flow                                                                                                                |
| `.start()`                         | Starts the Flow. This will start all its Executors and check if they are ready to be used.                                                 |
| `.close()`                         | Stops and closes the Flow. This will stop and shutdown all its Executors.                                                                                          |
| `with` context manager             | Use the Flow as a context manager. It will automatically start and stop your Flow.                                         |                                                                |
| `.plot()`                          | Visualizes the Flow. Helpful for building complex pipelines.                                                                                 |
| `.post()`                          | Sends requests to the Flow API.                                                                                                     |
| `.block()`                         | Blocks execution until the program is terminated. This is useful to keep the Flow alive so it can be used from other places (clients, etc). |
| `.to_docker_compose_yaml()`        | Generates a Docker-Compose file listing all its Executors as Services.                                                                       |
| `.to_kubernetes_yaml(<output_directory>)` | Generates the Kubernetes configuration files in `<output_directory>`. Based on your local Jina version, Jina Hub may rebuild the Docker image during the YAML generation process. If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`. |
| `.dry_run()`                       | Calls the dry run endpoint of the Flow to check if the Flow is ready to process requests. Returns a boolean indicating the readiness |

## Why should you use a Flow?

Once you have learned DocumentArray and Executor, you are able to split your multi-modal/cross-modal application into different independent modules and services.
But you need to chain them together in order to bring real value and to build and serve an application. That's exactly what Flows enable you to do.

- Flows connect microservices (Executors) to build a service with proper client/server style interface over HTTP, gRPC, or Websocket

- Flows let you scale these Executors independently to adjust to your requirements

- Flows allow you to easily use other cloud-native orchestrators, such as Kubernetes, to manage your service

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


f = Flow(port=12345).add(name='myexec1', uses=MyExecutor)

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
add-executors
topologies
flow-api
monitoring-flow
health-check
when-things-go-wrong
yaml-spec
```
