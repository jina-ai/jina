(deployment)=
# Deployment

A {class}`~jina.Deployment` orchestrates a single {class}`~jina.Executor` to accomplish a task.
Documents are processed by Executors.

You can think of a Deployment as an interface to configure and launch your {ref}`microservice architecture <architecture-overview>`,
while the heavy lifting is done by the {ref}`service <executor-cookbook>` itself.
In particular, each Deployment also launches a {ref}`Gateway <gateway>` service, which can expose the service through an API that you define.

The most important methods of the `Deployment` object are the following:

| Method                                                       | Description                                                                                                                                                                                                                                                                          |
|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| {meth}`~jina.Deployment.start()`                                   | Starts the Deployment. This will start all its Executors and check if they are ready to be used.                                                                                                                                                                                           |
| {meth}`~jina.Deployment.close()`                                   | Stops and closes the Deployment. This will stop and shutdown all its Executors.                                                                                                                                                                                                            |
| `with` context manager                                       | Uses the Deployment as a context manager. It will automatically start and stop your Deployment.                                                                                                                                                                                                   |                                                                |
| {meth}`~jina.clients.mixin.PostMixin.post()`                 | Sends requests to the Deployment API.                                                                                                                                                                                                                                                      |
| {meth}`~jina.Deployment.block()`                                   | Blocks execution until the program is terminated. This is useful to keep the Deployment alive so it can be used from other places (clients, etc).                                                                                                                                          |
| {meth}`~jina.Deployment.to_docker_compose_yaml()`                  | Generates a Docker-Compose file listing all Executors as services.                                                                                                                                                                                                                                                |
| {meth}`~jina.Deployment.to_kubernetes_yaml()`                      | Generates Kubernetes configuration files in `<output_directory>`. Based on your local Jina version, Executor Hub may rebuild the Docker image during the YAML generation process. If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.                                                                                                                                   |
| {meth}`~jina.clients.mixin.HealthCheckMixin.is_deployment_ready()` | Check if the Deployment is ready to process requests. Returns a boolean indicating the readiness.                                                                                                                                                                                                                                                                                                                                 |

## Why should you use a Deployment?

Once you've learned DocumentArray and Executor, you can split a big task into small independent modules and services.

- Deployments let you scale these Executors independently to match your requirements.

- Deployments let you easily use other cloud-native orchestrators, such as Kubernetes, to manage your service.

## Minimum working example

````{tab} Pythonic style


```python
from jina import Deployment, Executor, requests, Document


class MyExecutor(Executor):
    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


dep = Deployment(name='myexec1', uses=MyExecutor)

with dep:
    dep.post(on='/bar', inputs=Document(), on_done=print)
```


````

````{tab} Deployment-as-a-Service style

Server:

```python
from jina import Deployment, Executor, requests


class MyExecutor(Executor):
    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


dep = Deployment(port=12345, name='myexec1', uses=MyExecutor)

with dep:
    dep.block()
```

Client:

```python
from jina import Client, Document

c = Client(port=12345)
c.post(on='/bar', inputs=Document(), on_done=print)
```

````

````{tab} Load from YAML

`deployment.yml`:
```yaml
jtype: Deployment
name: myexec1
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
from jina import Deployment, Document

dep = Deployment.load_config('deployment.yml')

with dep:
    try:
        dep.post(on='/bar', inputs=Document(), on_done=print)
    except Exception as ex:
        # handle exception
        pass
```

````

```{caution}
The statement `with dep:` starts the Deployment, and exiting the indented with block stops the Deployment, including its Executors.
Exceptions raised inside the `with dep:` block will close the Deployment context manager. If you don't want this, use a `try...except` block to surround the statements that could potentially raise an exception.
```
