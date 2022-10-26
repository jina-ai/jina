(serve-executor-standalone)=
# Serve

Executors can be served - and remotely accessed - directly, without the need to instantiate a Flow manually.
This is especially useful when debugging an Executor in a remote setting. It can also be used to run external/shared Executors to be used in multiple Flows.
There are different options how you can deploy and run a stand-alone Executor:
* Run the Executor directly from Python with the `.serve()` class method
* Run the static `Executor.to_kubernetes_yaml()` method to generate K8s deployment configuration files
* Run the static `Executor.to_docker_compose_yaml()` method to generate a docker-compose service file

## Serve directly
An Executor can be served using the `.serve()` class method:

````{tab} Serve Executor

```python
from jina import Executor, requests
from docarray import DocumentArray, Document


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

```console
['executed MyExec']
```

````

Internally, the `.serve()` method creates a Flow and starts it. Therefore, it can take all associated parameters:
`uses_with`, `uses_metas`, `uses_requests` are passed to the internal `flow.add()` call, `stop_event` is an Event that stops
the Executor, and `**kwargs` is passed to the internal `Flow()` initialisation call.

````{admonition} See Also
:class: seealso

For more details on these arguments and the workings of `Flow`, see the {ref}`Flow section <flow-cookbook>`.
````

## Serve via Kubernetes
You can generate Kubernetes configuration files for your containerized Executor by using the static `Executor.to_kubernetes_yaml()` method. This works very similar to {ref}`deploying a Flow in Kubernetes <kubernetes>`, because your Executor is wrapped automatically in a Flow and using the very same deployment techniques.

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
The above example will deploy the `DummyHubExecutor` from Jina Hub into your Kubernetes cluster.

````{admonition} Hint
:class: hint
The Executor you are using needs to be already containerized and stored in a registry accessible from your Kubernetes cluster. We recommend Jina Hub for this.
````

(external-shared-executor)=
### External and shared Executors
The type of stand-alone Executors can be either *external* or *shared*. By default, it will be external.
An external Executor is deployd alongside a {ref}`Gateway <architecture-overview>`. 
A shared Executor has no Gateway. Both types of Executor {ref}`can be used directly in any Flow <external-executor>`.
Having a Gateway may be useful if you want to be able to access your Executor with the {ref}`Client <client>` without an additional Flow. If the Executor will only be used inside other Flows, you should define a shared Executor to save the costs of running the Gateway Pod in Kubernetes.

## Serve via Docker Compose
You can generate a Docker Compose service file for your containerized Executor by using the static `Executor.to_docker_compose_yaml()` method. This works very similar to {ref}`running a Flow with Docker Compose <docker-compose>`, because your Executor is wrapped automatically in a Flow and using the very same deployment techniques.

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
The above example will run the `DummyHubExecutor` from Jina Hub locally on your computer using Docker Compose.

````{admonition} Hint
:class: hint
The Executor you are using needs to be already containerized and stored in an accessible registry. We recommend Jina Hub for this.
````

