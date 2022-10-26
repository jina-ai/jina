(flow)=

# Configure Flow

**Flow** ties Executors together into a processing pipeline, provides scalability and facilitates deployments in the cloud.
Every `Flow` provides an API to receive requests over the network. Supported protocols are gRPC, HTTP and WebSocket.

There are two ways of defining a Flow, either directly from the Python API or using yaml files. For each section we will show you both possibles way of configuring your flow.

```{admonition} Jina Client
:class: caution

To showcase the workings of Flow, the examples below use a Client connecting to it, all from withing the same Pyhon script.

In most cases, this is not how a real user would access a Flow. Rather, they would use one of {ref}`several ways of connecting over a network<access-flow-api>`.
This does not affect how you have to configure your Flow API, so the examples here should translate seamlessly.

For more proper use of the Client, and more information about the Client itself, see the {ref}`Client documentation <client>`.
```

(flow-protocol)=
## Serve Flow with different protocols
You can use three different protocols to serve the `Flow`: `grpc`,`http` and `websocket`

````{tab} gRPC

```{code-block} python
---
emphasize-lines: 11, 13
---

from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests


class FooExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was called'))


f = Flow(protocol='grpc', port=12345).add(uses=FooExecutor)
with f:
    client = Client(port=12345)
    docs = client.post(on='/')
    print(docs.texts)
```

```text
['foo was called']
```
````

````{tab} HTTP
```{code-block} python
---
emphasize-lines: 11, 13
---

from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests


class FooExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was called'))


f = Flow(protocol='http', port=12345).add(uses=FooExecutor)
with f:
    client = Client(port=12345, protocol='http')
    docs = client.post(on='/')
    print(docs.texts)
```

```text
['foo was called']
```

````

````{tab} WebSocket

```{code-block} python
---
emphasize-lines: 11, 13
---

from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests


class FooExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was called'))


f = Flow(protocol='websocket', port=12345).add(uses=FooExecutor)
with f:
    client = Client(port=12345, protocol='websocket')
    docs = client.post(on='/')
    print(docs.texts)
```

```text
['foo was called']
```
````


To configure the protocol using a YAML file, just do


````{tab} gRPC
Note that gRPC is the default protocol, so you can just omit it.
```{code-block} yaml
jtype: Flow
with:
  protocol: 'grpc'
```

````

````{tab} HTTP
```{code-block} yaml
jtype: Flow
with:
  protocol: 'http'
```


````

````{tab} WebSocket

```{code-block} yaml
jtype: Flow
with:
  protocol: 'websocket'
```

````


(custom-http)=
## Customize HTTP interface

Not every Executor endpoint will automatically be exposed through the external HTTP interface.
By default, any Flow exposes the following CRUD and debug HTTP endpoints: `/status`, `/post`, `/index`, `/search`, `/update`, and `/delete`.

Executors that provide additional endpoints (e.g. `/foo`) will be exposed only after manual configuration.
These custom endpoints can be added to the HTTP interface using `Flow.expose_endpoint`.

```{figure} expose-endpoints.svg
:align: center
```
````{tab} Python

```python
from jina import Executor, requests, Flow


class MyExec(Executor):
    @requests(on='/foo')
    def foo(self, docs, **kwargs):
        pass


f = Flow(protocol='http').add(uses=MyExec)
f.expose_endpoint('/foo', summary='my endpoint')
with f:
    f.block()
```
````

````{tab} YAML
You can enable custom endpoints in a Flow using yaml syntax as well.
```yaml
jtype: Flow
with:
  protocol: http
  expose_endpoints:
    /foo:
      summary: my endpoint
```
````

Now, sending an HTTP data request to the `/foo` endpoint is equivalent to calling `f.post('/foo', ...)` using the Python Client.

You can add more `kwargs` to build richer semantics on your HTTP endpoint. Those meta information will be rendered by Swagger UI and be forwarded to the OpenAPI schema.
````{tab} Python

```python
f.expose_endpoint('/bar', summary='my endpoint', tags=['fine-tuning'], methods=['PUT'])
```
````

````{tab} YAML
```yaml
jtype: Flow
with:
  protocol: http
  expose_endpoints:
    /bar:
      methods: ["PUT"]
      summary: my endpoint
      tags:
        - fine-tuning
```
````
### Hide default endpoints from HTTP interface

It is possible to hide the default CRUD and debug endpoints in production. This might be useful when the context is not applicable.
For example, in the code snippet below, we didn't implement any CRUD endpoints for the executor, hence it does not make sense to expose them to public.
````{tab} Python
```python
from jina import Flow

f = Flow(protocol='http', no_debug_endpoints=True, no_crud_endpoints=True)
```
````

````{tab} YAML
```yaml
jtype: Flow
with:
  protocol: 'http'
  no_debug_endpoints: True, 
  no_crud_endpoints: True
```
````

After setting up a Flow in this way, the {ref}`default HTTP endpoints <custom-http>` will not be exposed.

(cors)=
### Enable Cross-Origin Resource Sharing (CORS)

To make a Flow accessible from a website with a different domain, you need to enable [Cross-Origin Resource Sharing (CORS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS).
Among other things, CORS is necessary to provide a {ref}`Swagger UI interface <swagger-ui>` for your Flow.

Note that CORS is disabled by default, for security reasons.
To enable CORS, configure your Flow in the following way:
```python
from jina import Flow

f = Flow(cors=True, protocol='http')
```

### Advanced configuration options

HTTP support in Jina is powered by [Uvicorn](https://www.uvicorn.org/).
You can configure the Flow's internal Uvicorn sever to your heart's content by passing `uvicorn_kwargs` to the Flow:

```python
from jina import Flow

f = Flow(protocol='http', uvicorn_kwargs={'loop': 'asyncio', 'http': 'httptools'})
```

These arguments will be directly passed to the Uvicorn server.

````{admonition} See Also
:class: seealso

For more details about the arguments that are used here, and about other available settings for the Uvicorn server,
see their [website](https://www.uvicorn.org/settings/).

````


## Add GraphQL endpoint

````{admonition} Caution
:class: caution

GraphQL support is an optional feature that requires optional dependencies.
To install these, run `pip install jina[graphql]` or `pip install jina[all]`.

Unfortunately, these dependencies are **not available through Conda**. You will have to use `pip` to be able to use GraphQL
feature.
````

A Flow can optionally expose a [GraphQL](https://graphql.org/) endpoint, located at `/graphql`.
To enable this endpoint, all you need to do is set `expose_graphql_endpoint=True` on your HTTP Flow:


````{tab} Python

```python
from jina import Flow

f = Flow(protocol='http', expose_graphql_endpont=True)
```
````

````{tab} YAML
```yaml
jtype: Flow
with:
  protocol: 'http'
  expose_graphql_endpont: True, 
```
````


````{admonition} See Also
:class: seealso

For more details about the Jina GraphQL enpoint, see {ref}`here <flow-graphql>`.
````



(flow-tls)=
## Enable TLS

You can enable TLS encryption between your Flow's Gateway and a Client, for any of the protocols supported by Jina (HTTP, gRPC, and Websocket).

````{admonition} Caution
:class: caution
Enabling TLS will encrypt the data that is transferred between the Flow and the Client.
Data that is passed between the microservices configured by the Flow, such as Executors, will **not** be encrypted.
````

To enable TLS encryption, you need to pass a valid *keyfile* and *certfile* to the Flow, using the `ssl_keyfile` `ssl_certfile`
parameters:

```python
PORT = ...

f = Flow(
    port=PORT,
    ssl_certfile='path/to/certfile.crt',
    ssl_keyfile='path/to/keyfile.crt',
)
```

If both of these are provided, the Flow will automatically configure itself to use TLS encryption for its communication with any Client.


## Limit outstanding requests

By default, Jina's Client sens requests to the Flow as fast as possible, without any throttling.
If a client sends his request faster than the Flow can process them, this can put a lot of loan on the Flow.
Typically, this is most likely to happen for expensive index Flows. 

You can control the number of in flight requests per Client with the `prefetch` argument, e.g. setting `prefetch=2` lets the API accept only 2 requests per client in parallel, hence limiting the load. By default, prefetch is disabled (set to 0).

```{code-block} python
---
emphasize-lines: 8, 10
---

def requests_generator():
    while True:
        yield Document(...)

class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        slow_operation()

# Makes sure only 2 requests reach the Executor at a time.
with Flow(prefetch=2).add(uses=MyExecutor) as f:
    f.post(on='/', inputs=requests_generator)
```

```{danger}
When working with very slow executors and a big amount of data, you must set `prefetch` to some small number to prevent out of memory problems. If you are unsure, always set `prefetch=1`.
```


````{tab} Python

```python
from jina import Flow

f = Flow(protocol='http', cors=True)
```
````

````{tab} YAML
```yaml
jtype: Flow
with:
  protocol: 'http'
  cors: True, 
```
````



## Generate deployment configuration

To deploy a `Flow` you will need to deploy the Executors it is composed of.
The `Flow` is offering convenience functions to generate the necessary configuration files for some use cases.
At the moment, `Docker-Compose` and `Kubernetes` are supported.

```{admonition} See also
:class: seealso
For more in-depth guides on Flow deployment, take a look at our how-tos for {ref}`Docker-compose <docker-compose>` and
{ref}`Kubernetes <kubernetes>`.
```

\
**Docker-Compose**
```python
from jina import Flow

f = Flow().add()
f.to_docker_compose_yaml()
```
This will generate a single `docker-compose.yml` file containing all the `Executors` of the `Flow`.

\
**Kubernetes**
```python
from jina import Flow

f = Flow().add()
f.to_k8s_yaml('flow_k8s_configuration')
```
This will generate the necessary Kubernetes configuration files for all the `Executors` of the `Flow`.
The generated folder can be used directly with `kubectl` to deploy the `Flow` to an existing Kubernetes cluster.

Based on your local Jina version, Jina Hub may rebuild the Docker image during the YAML generation process.
If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.

## See further

- {ref}`Access the Flow with the Client <client>`
- {ref}`Deployment with Kubernetes <kubernetes>` 
- {ref}`Deployment with Docker Compose <docker-compose>`
- {ref}`Executors inside a Flow <executor-in-flow>`
