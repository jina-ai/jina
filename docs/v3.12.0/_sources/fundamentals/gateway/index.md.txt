(flow)=

# Gateway

Every {class}`~jina.Flow` provides an API Gateway to receive requests over the network. Supported protocols are gRPC, HTTP and WebSocket with TLS.

There are two ways of defining a Gateway, either directly from the Python or using YAML. The full YAML specification of Gateway can be {ref}`found here<yaml-spec>`.

```{toctree}
:hidden:

yaml-spec
```


(flow-protocol)=
## Supported protocols
You can use three different protocols to serve the `Flow`: gRPC, HTTP and Websocket.

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
## Serve multiple protocols at the same time:
You can use multiple protocols in the same gateway, serve your Flow using multiple protocols and bind it 
to several ports:

````{tab} Python
```{code-block} python
---
emphasize-lines: 2
---
from jina import Flow
flow = Flow(port=[12345, 12344, 12343], protocol=['grpc', 'http', 'websocket'])
with flow:
    flow.block()
```
````

````{tab} YAML
```{code-block yaml}
jtype: Flow
with:
  protocol:
    - 'grpc'
    - 'http'
    - 'websocket'
  port:
    - 12345
    - 12344
    - 12343
```
````

```{figure} multi-protocol-flow.png
:width: 70%
```

```{admonition} Important
:class: important

In case you want to serve a Flow using multiple protocols, make sure to specify as much ports as protocols used. 
```

(custom-http)=
## Customize HTTP interface

Not every {class}`~jina.Executor` endpoint will automatically be exposed through the external HTTP interface.
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

However, if you want to send requests to a different Executor endpoint, you can still do it without exposing it in the HTTP endpoint, by sending an HTTP request to the `/post` HTTP endpoint while setting  
`execEndpoint` in the request.

```text
curl --request POST \
'http://localhost:12345/post' \
--header 'Content-Type: application/json' -d '{"data": [{"text": "hello world"}], "execEndpoint": "/foo"}'
```

The above cURL command is equivalent to passing the `on` parameter to `client.post` as follows:

```python
from docarray import DocumentArray, Document
from jina import Client

client = Client(port=12345, protocol='http')
client.post(on='/foo', inputs=DocumentArray([Document(text='hello world')]))
```

### Hide default endpoints

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
### Enable cross-origin resource sharing

To make a Flow accessible from a website with a different domain, you need to enable [Cross-Origin Resource Sharing (CORS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS).
Among other things, CORS is necessary to provide a {ref}`Swagger UI interface <swagger-ui>` for your Flow.

Note that CORS is disabled by default, for security reasons.
To enable CORS, configure your Flow in the following way:
```python
from jina import Flow

f = Flow(cors=True, protocol='http')
```

### Advanced options

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








## Get status

```{tip}
Though you can run Executors, Gateway and Client in different Jina versions, it is recommended to work with the same Jina version.
```

Gateway provides an endpoint that exposes relevant information about the environment where it runs. 

This information exposes information in a dict-like structure with the following keys:
- `jina`: A dictionary containing information about the system and the versions of several packages including jina package itself
- `envs`: A dictionary containing all the values if set of the {ref}`environment variables used in Jina <jina-env-vars>`


### Use gRPC


To see how this works, first instantiate a Flow with an Executor exposed to a specific port and block it for serving:

```python
from jina import Flow

PROTOCOL = 'grpc'  # it could also be http or websocket

with Flow(protocol=PROTOCOL, port=12345).add() as f:
    f.block()
```

Then, you can use [grpcurl](https://github.com/fullstorydev/grpcurl)  sending status check request to the Gateway.

```shell
docker pull fullstorydev/grpcurl:latest
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaInfoRPC/_status
```

The error-free output below signifies a correctly running Gateway:

```json
{
  "jina": {
    "architecture": "######",
    "ci-vendor": "######",
    "docarray": "######",
    "grpcio": "######",
    "jina": "######",
    "jina-proto": "######",
    "jina-vcs-tag": "######",
    "platform": "######",
    "platform-release": "######",
    "platform-version": "######",
    "processor": "######",
    "proto-backend": "######",
    "protobuf": "######",
    "python": "######", 
    "pyyaml": "######",
    "session-id": "######",
    "uid": "######",
    "uptime": "######"
  },
  "envs": {
    "JINA_AUTH_TOKEN": "(unset)",
    "JINA_DEFAULT_HOST": "(unset)",
    "JINA_DEFAULT_TIMEOUT_CTRL": "(unset)",
    "JINA_DEPLOYMENT_NAME": "(unset)",
    "JINA_DISABLE_HEALTHCHECK_LOGS": "(unset)",
    "JINA_DISABLE_UVLOOP": "(unset)",
    "JINA_EARLY_STOP": "(unset)",
    "JINA_FULL_CLI": "(unset)",
    "JINA_GATEWAY_IMAGE": "(unset)",
    "JINA_GRPC_RECV_BYTES": "(unset)",
    "JINA_GRPC_SEND_BYTES": "(unset)",
    "JINA_HUBBLE_REGISTRY": "(unset)",
    "JINA_HUB_NO_IMAGE_REBUILD": "(unset)",
    "JINA_LOCKS_ROOT": "(unset)",
    "JINA_LOG_CONFIG": "(unset)",
    "JINA_LOG_LEVEL": "(unset)",
    "JINA_LOG_NO_COLOR": "(unset)",
    "JINA_MP_START_METHOD": "(unset)",
    "JINA_RANDOM_PORT_MAX": "(unset)",
    "JINA_RANDOM_PORT_MIN": "(unset)"
  }
}
```

```{tip}
You can also use it to check Executor status, as Executor's communication protocol is gRPC.
```

### Use HTTP/Websocket

When using HTTP or Websocket as the Gateway protocol, you can use curl to target the `/status` endpoint and get the Jina info.

```shell
curl http://localhost:12345/status
```

```json
{"jina":{"jina":"######","docarray":"######","jina-proto":"######","jina-vcs-tag":"(unset)","protobuf":"######","proto-backend":"######","grpcio":"######","pyyaml":"######","python":"######","platform":"######","platform-release":"######","platform-version":"######","architecture":"######","processor":"######","uid":"######","session-id":"######","uptime":"######","ci-vendor":"(unset)"},"envs":{"JINA_AUTH_TOKEN":"(unset)","JINA_DEFAULT_HOST":"(unset)","JINA_DEFAULT_TIMEOUT_CTRL":"(unset)","JINA_DEPLOYMENT_NAME":"(unset)","JINA_DISABLE_UVLOOP":"(unset)","JINA_EARLY_STOP":"(unset)","JINA_FULL_CLI":"(unset)","JINA_GATEWAY_IMAGE":"(unset)","JINA_GRPC_RECV_BYTES":"(unset)","JINA_GRPC_SEND_BYTES":"(unset)","JINA_HUBBLE_REGISTRY":"(unset)","JINA_HUB_NO_IMAGE_REBUILD":"(unset)","JINA_LOG_CONFIG":"(unset)","JINA_LOG_LEVEL":"(unset)","JINA_LOG_NO_COLOR":"(unset)","JINA_MP_START_METHOD":"(unset)","JINA_RANDOM_PORT_MAX":"(unset)","JINA_RANDOM_PORT_MIN":"(unset)","JINA_DISABLE_HEALTHCHECK_LOGS":"(unset)","JINA_LOCKS_ROOT":"(unset)"}}
```

(server-compress)=
## Add gRPC compression

The communication between {class}`~jina.Executor`s inside a {class}`~jina.Flow` is done via gRPC. To optimize the performance and the bandwidth of these connections,
Jina allows the users to specify their [compression](https://grpc.github.io/grpc/python/grpc.html#compression) by specifying `compression` argument to the Flow.

The supported methods are: none, `gzip` and `deflate`.

```python
from jina import Flow

f = Flow(compression='gzip').add(...)
```

Note that this setting is only effective the internal communication of the Flow.
One can also specify the compression between client and gateway {ref}`as described here<client-compress>`.

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

(prefetch)=
## Limit outstanding requests

By default, Jina’s {class}`~jina.Client` sends requests to the Flow as fast as possible without any delay. If a client sends their request faster than the {class}`~jina.Flow` can process them, this can put a high load on the Flow. Typically, this is most likely to happen for Flows with expensive indexing.

You can control the number of in flight requests per Client with the `prefetch` argument. E.g. setting `prefetch=2` lets the API accept only 2 requests per client in parallel, hence limiting the load. By default, prefetch is set to 1000. To disable it you can set it to 0.

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

f = Flow(protocol='http', cors=True, prefetch=10)
```
````

````{tab} YAML
```yaml
jtype: Flow
with:
  protocol: 'http'
  cors: True,
  prefetch: 10
```
````

## Set timeouts

You can set timeouts for sending requests to the {class}`~jina.Executor`s within a {class}`~jina.Flow` by passing the `timeout_send` parameter. The timeout is specified in milliseconds. By default, it is `None` and the timeout is disabled.

If you use timeouts, you may also need to set the {ref}`prefetch <prefetch>` option in the Flow. Otherwise, requests may queue up at an Executor and eventually time out.

```{code-block} python
with Flow(timeout_send=1000) as f:
    f.post(on='/', inputs=[Document()])
```
The example above limits every request to the Executors in the Flow to a timeout of 1 second.


## GraphQL support

````{admonition} Caution
:class: caution

GraphQL support is an optional feature that requires optional dependencies.
To install these, run `pip install jina[graphql]` or `pip install jina[all]`.

Unfortunately, these dependencies are **not available through Conda**. You will have to use `pip` to be able to use GraphQL
feature.
````

A {class}`~jina.Flow` can optionally expose a [GraphQL](https://graphql.org/) endpoint, located at `/graphql`.
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


## See further

- {ref}`Access the Flow with the Client <client>`
- {ref}`Deployment with Kubernetes <kubernetes>` 
- {ref}`Deployment with Docker Compose <docker-compose>`
- {ref}`Executors inside a Flow <executor-in-flow>`

