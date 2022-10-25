(flow-cookbook)=
# Flow

A {class}`~jina.Flow` orchestrates Executors into a processing pipeline to build a multi-modal/cross-modal application.
Documents "flow" through the created pipeline and are processed by Executors.

You can think of Flow as an interface to configure and launch your {ref}`microservice architecture <architecture-overview>`,
while the heavy lifting is done by the {ref}`services <executor-cookbook>` themselves.
In particular, each Flow also launches a *Gateway* service, which can expose all other services through an API that you define.


The most important methods of the `Flow` object are the following:

| Method                                                       | Description                                                                                                                                                                                                                                                                          |
|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| {meth}`~jina.Flow.add`                                       | Add an Executor to the Flow                                                                                                                                                                                                                                                          |
| {meth}`~jina.Flow.start()`                                   | Starts the Flow. This will start all its Executors and check if they are ready to be used.                                                                                                                                                                                           |
| {meth}`~jina.Flow.close()`                                   | Stops and closes the Flow. This will stop and shutdown all its Executors.                                                                                                                                                                                                            |
| `with` context manager                                       | Use the Flow as a context manager. It will automatically start and stop your Flow.                                                                                                                                                                                                   |                                                                |
| {meth}`~jina.Flow.plot()`                                    | Visualizes the Flow. Helpful for building complex pipelines.                                                                                                                                                                                                                         |
| {meth}`~jina.clients.mixin.PostMixin.post()`                 | Sends requests to the Flow API.                                                                                                                                                                                                                                                      |
| {meth}`~jina.Flow.block()`                                   | Blocks execution until the program is terminated. This is useful to keep the Flow alive so it can be used from other places (clients, etc).                                                                                                                                          |
| {meth}`~jina.Flow.to_docker_compose_yaml()`                  | Generates a Docker-Compose file listing all its Executors as Services.                                                                                                                                                                                                               |
| {meth}`~jina.Flow.to_kubernetes_yaml()`                      | Generates the Kubernetes configuration files in `<output_directory>`. Based on your local Jina version, Jina Hub may rebuild the Docker image during the YAML generation process. If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`. |
| {meth}`~jina.clients.mixin.HealthCheckMixin.is_flow_ready()` | Check if the Flow is ready to process requests. Returns a boolean indicating the readiness                                                                                                                                                                                           |

## Why should you use a Flow?

Once you have learned DocumentArray and Executor, you are able to split your multi-modal/cross-modal application into different independent modules and services.
But you need to chain them together in order to bring real value and to build and serve an application. That's exactly what Flows enable you to do.

- Flows connect microservices (Executors) to build a service with proper client/server style interface over HTTP, gRPC, or Websocket

- Flows let you scale these Executors independently to adjust to your requirements

- Flows allow you to easily use other cloud-native orchestrators, such as Kubernetes, to manage your service

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
    f.post(on='/bar', inputs=Document(), on_done=print)
```

````




```{toctree}
:hidden:

create-flow
add-executors
topologies
monitoring-flow
health-check
when-things-go-wrong
yaml-spec
```
