(serve-executor-standalone)=
# Serve

{class}`~jina.Executor`s can be served - and remotely accessed - directly, without instantiating a Flow manually.
This is especially useful when debugging an Executor in a remote setting. It can also be used to run external/shared Executors to be used in multiple Flows.

There are different options for deploying and running a standalone Executor:
* Run the Executor directly from Python with the `.serve()` class method
* Run the static {meth}`~jina.serve.executors.BaseExecutor.to_kubernetes_yaml()` method to generate K8s deployment configuration files
* Run the static {meth}`~jina.serve.executors.BaseExecutor.to_docker_compose_yaml()` method to generate a Docker Compose service file

````{admonition} Served vs. shared Executor
:class: hint

In Jina there are two ways of running standalone Executors: *Served Executors* and *shared Executors*.

- A **served Executor** is launched by one of the following methods: `.serve()`, `to_kubernetes_yaml()`, or `to_docker_compose_yaml()`.
It resides behind a {ref}`Gateway <architecture-overview>` and can thus be directly accessed by a {ref}`Client <client>`.
It can also be used as part of a Flow.

- A **shared Executor** is launched using the [Jina CLI](../cli/index.rst) and does *not* sit behind a Gateway.
It is intended to be used in one or more Flows.
Because a shared Executor does not reside behind a Gataway, it cannot be directly accessed by a Client, but it requires
fewer networking hops when used inside of a Flow.

Both served and shared Executors can be used as part of a Flow, by adding them as an {ref}`external Executor <external-executors>`.

````

## Serve directly
An {class}`~jina.Executor` can be served using the {meth}`~jina.serve.executors.BaseExecutor.serve` method:

````{tab} Serve Executor

```python
from docarray import DocumentArray, Document
from jina import Executor, requests


class MyExec(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0] = 'executed MyExec'  # custom logic goes here


MyExec.serve(port=12345)
```

````

````{tab} Access served Executor

```python
from jina import Client, DocumentArray, Document

print(Client(port=12345).post(inputs=DocumentArray.empty(1), on='/foo').texts)
```

```shell
['executed MyExec']
```

````

Internally, the {meth}`~jina.serve.executors.BaseExecutor.serve` method creates and starts a {class}`~jina.Flow`. Therefore, it can take all associated parameters:
`uses_with`, `uses_metas`, `uses_requests` are passed to the internal {meth}`~jina.serve.executors.BaseExecutor.add` call, `stop_event` stops
the Executor, and `**kwargs` is passed to the internal {meth}`~jina.Flow` initialisation call.

````{admonition} See Also
:class: seealso

For more details on these arguments and the workings of a Flow, see the {ref}`Flow section <flow-cookbook>`.
````

## Serve via Kubernetes
You can generate Kubernetes configuration files for your containerized Executor by using the static `Executor.to_kubernetes_yaml()` method. This works like {ref}`deploying a Flow in Kubernetes <kubernetes>`, because your Executor is wrapped automatically in a Flow and uses the very same deployment techniques.

```python
from jina import Executor

Executor.to_kubernetes_yaml(
    output_base_path='/tmp/config_out_folder',
    port_expose=8080,
    uses='jinahub+docker://DummyHubExecutor',
    executor_type=Executor.StandaloneExecutorType.EXTERNAL,
)
```
```shell
kubectl apply -R -f /tmp/config_out_folder
```
The above example deploys the `DummyHubExecutor` from Executor Hub into your Kubernetes cluster.

````{admonition} Hint
:class: hint
The Executor you use needs to be already containerized and stored in a registry accessible from your Kubernetes cluster. We recommend Executor Hub for this.
````

(external-shared-executor)=
### External and shared Executors
This type of standalone Executor can be either *external* or *shared*. By default, it is external.

- An external Executor is deployed alongside a {ref}`Gateway <architecture-overview>`. 
- A shared Executor has no Gateway. 

Both types of Executor {ref}`can be used directly in any Flow <external-executor>`.
Having a Gateway may be useful if you want to be able to access your Executor with the {ref}`Client <client>` without an additional Flow. If the Executor is only used inside other Flows, you should define a shared Executor to save the costs of running the Gateway Pod in Kubernetes.

## Serve via Docker Compose
You can generate a Docker Compose service file for your containerized Executor by using the static {meth}`~jina.serve.executors.BaseExecutor.to_docker_compose_yaml` method. This works like {ref}`running a Flow with Docker Compose <docker-compose>`, because your Executor is wrapped automatically in a Flow and uses the very same deployment techniques.

```python
from jina import Executor

Executor.to_docker_compose_yaml(
    output_path='/tmp/docker-compose.yml',
    port_expose=8080,
    uses='jinahub+docker://DummyHubExecutor',
)
```
```shell
docker-compose -f /tmp/docker-compose.yml up
```
The above example runs the `DummyHubExecutor` from Executor Hub locally on your computer using Docker Compose.

````{admonition} Hint
:class: hint
The Executor you use needs to be already containerized and stored in an accessible registry. We recommend Executor Hub for this.
````

