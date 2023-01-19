(serve-executor-standalone)=
# Serve

{class}`~jina.Executor`s can be served and accessed over gRPC, allowing you to use them to create a gRPC-based service for various tasks such as model inference, data processing, generative AI, and search services.

There are different options for deploying and running a standalone Executor:
* Run the Executor directly from Python with the {class}`~jina.orchestrate.deployments.Deployment` class
* Run the static {meth}`~jina.serve.executors.BaseExecutor.to_kubernetes_yaml()` method to generate Kubernetes deployment configuration files
* Run the static {meth}`~jina.serve.executors.BaseExecutor.to_docker_compose_yaml()` method to generate a Docker Compose service file



```{seealso}
Executors can also be combined to form a pipeline of microservices. We will see in a later step how 
to achieve this with the {ref}`Flow <flow-cookbook>`
```

````{admonition} Served vs. shared Executor
:class: hint

In Jina there are two ways of running standalone Executors: *Served Executors* and *shared Executors*.

- A **served Executor** is launched by one of the following methods: {class}`~jina.orchestrate.deployments.Deployment`, `to_kubernetes_yaml()`, or `to_docker_compose_yaml()`.
It resides behind a {ref}`Gateway <architecture-overview>` and can thus be directly accessed by a {ref}`Client <client>`.
It can also be used as part of a Flow.

- A **shared Executor** is launched using the [Jina CLI](../../cli/index.rst) and does *not* sit behind a Gateway.
It is intended to be used in one or more Flows.
Because a shared Executor does not reside behind a Gataway, it cannot be directly accessed by a Client, but it requires
fewer networking hops when used inside of a Flow.

Both served and shared Executors can be used as part of a Flow, by adding them as an {ref}`external Executor <external-executors>`.

````

## Serve directly
An {class}`~jina.Executor` can be served using the {class}`~jina.orchestrate.deployments.Deployment` class.

The {class}`~jina.orchestrate.deployments.Deployment` class aims to separate the deployment configuration from the serving logic.
In other words:
* the Executor cares about defining the logic to serve, which endpoints to define and what data to accept.
* the Deployment layer cares about how to orchestrate this service, how many replicas or shards, etc.

This separation also aims to enhance the reusability of Executors: the same implementation of an Executor can be 
served in multiple ways/configurations using Deployment.

````{tab} Python class

```python
from docarray import DocumentArray, Document
from jina import Executor, requests, Deployment


class MyExec(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'executed MyExec'  # custom logic goes here


with Deployment(uses=MyExec, port=12345, replicas=2) as dep:
    docs = dep.post(on='/foo', inputs=DocumentArray.empty(1))
    print(docs.texts)
```
````

````{tab} YAML configuration
`executor.yaml`:
```
jtype: MyExec
py_modules:
    - executor.py
```

```python
from jina import Deployment

with Deployment(uses='executor.yaml', port=12345, replicas=2) as dep:
    docs = dep.post(on='/foo', inputs=DocumentArray.empty(1))
    print(docs.texts)
```
````

````{tab} Hub Executor

```python
from jina import Deployment

with Deployment(uses='jinaai://my-username/MyExec/', port=12345, replicas=2) as dep:
    docs = dep.post(on='/foo', inputs=DocumentArray.empty(1))
    print(docs.texts)
```

````

````{tab} Docker image

```python
from jina import Deployment

with Deployment(uses='docker://my-executor-image', port=12345, replicas=2) as dep:
    docs = dep.post(on='/foo', inputs=DocumentArray.empty(1))
    print(docs.texts)
```

````

```text
─────────────────────── 🎉 Deployment is ready to serve! ───────────────────────
╭────────────── 🔗 Endpoint ────────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:12345   │
│  🔒     Private     192.168.3.147:12345   │
│  🌍      Public    87.191.159.105:12345   │
╰───────────────────────────────────────────╯
['executed MyExec']
```

````{hint}
You can use `dep.block()` to serve forever:

```python
with Deployment(uses=MyExec, port=12345, replicas=2) as dep:
    dep.block()
```
````

The {class}`~jina.orchestrate.deployments.Deployment` class accepts configuration options similar to 
{ref}`Executor configuration with Flows <flow-configure-executors>`.

````{admonition} See Also
:class: seealso

For more details on these arguments and the workings of a Flow, see the {ref}`Flow section <flow-cookbook>`.
````

(kubernetes-executor)=
## Serve via Kubernetes
You can generate Kubernetes configuration files for your containerized Executor by using the {meth}`~jina.Deployment.to_kubernetes_yaml()` method. This works like {ref}`deploying a Flow in Kubernetes <kubernetes>`.

```python
from jina import Deployment

dep = Deployment(
    uses='jinaai+docker://jina-ai/DummyHubExecutor', port_expose=8080, replicas=3
)
dep.to_kubernetes_yaml('/tmp/config_out_folder', k8s_namespace='my-namespace')
```
```shell
kubectl apply -R -f /tmp/config_out_folder
```
The above example deploys the `DummyHubExecutor` from Executor Hub into your Kubernetes cluster.

````{admonition} Hint
:class: hint
The Executor you use needs to be already containerized and stored in a registry accessible from your Kubernetes cluster. We recommend Executor Hub for this.
````

Once the Executor is deployed, you can expose a service:
```bash
kubectl expose deployment executor --name=executor-exposed --type LoadBalancer --port 80 --target-port 8080 -n my-namespace
sleep 60 # wait until the external ip is configured
```

Let's export the external IP address created and use it to send requests to the Executor. 
```bash
export EXTERNAL_IP=`kubectl get service executor-exposed -n my-namespace -o=jsonpath='{.status.loadBalancer.ingress[0].ip}'`
```
To send requests using {meth}`~jina.Client`, make sure to set `stream=False` (note that this is only applicable and 
necessary for Kubernetes deployments of Executors):
```python
import os
from jina import Client, Document

host = os.environ['EXTERNAL_IP']
port = 80

client = Client(host=host, port=port)

print(client.post(on='/', inputs=Document(), stream=False).texts)
```

```text
['hello']
```

(external-shared-executor)=
### External and shared Executors
This type of standalone Executor can be either *external* or *shared*. By default, it is external.

- An external Executor is deployed alongside a {ref}`Gateway <architecture-overview>`. 
- A shared Executor has no Gateway. 

Both types of Executor {ref}`can be used directly in any Flow <external-executors>`.
Having a Gateway may be useful if you want to access your Executor with the {ref}`Client <client>` without an additional Flow. If the Executor is only used inside other Flows, you should define a shared Executor to save the costs of running the Gateway in Kubernetes.

## Serve via Docker Compose
You can generate a Docker Compose service file for your containerized Executor by using the static {meth}`~jina.serve.executors.BaseExecutor.to_docker_compose_yaml` method. This works like {ref}`running a Flow with Docker Compose <docker-compose>`, because your Executor is wrapped automatically in a Flow and uses the very same deployment techniques.

```python
from jina import Executor

Executor.to_docker_compose_yaml(
    output_path='/tmp/docker-compose.yml',
    port_expose=8080,
    uses='jinaai+docker://jina-ai/DummyHubExecutor',
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

