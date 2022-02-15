(flow)=

# Flow API

**Flow** ties Executors together into a processing pipeline, provides scalability and facilitates deployments in the cloud. Every `Flow` provides an API to receive requests over the network. Supported protocols are gRPC, HTTP and websockets. 

We recommend to use gRPC for the best performance, which is also the default protocol. Requests can be send via the Jina Python Client or separate clients like Curl. Flow streamlines and scales Executors.


````{tab} gRPC

```python
from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests

class FooExecutor(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))

f = Flow(protocol='grpc', port_expose=12345).add(uses=FooExecutor)
with f:
    client = Client(port=12345)
    response = client.post(on='/')
    print(response[0].data.docs.texts)
```
````

````{tab} HTTP
```python
from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests

class FooExecutor(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))

f = Flow(protocol='http', port_expose=12345).add(uses=FooExecutor)
with f:
    client = Client(port=12345, protocol='http')
    response = client.post(on='/')
    print(response[0].data.docs.texts)
    f.block()
```

```bash
 curl -X POST http://127.0.0.1:12345/search -H 'Content-type: application/json' -d '{"data":[{}]}'
```
````

````{tab} WebSocket

```python
from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests

class FooExecutor(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))

f = Flow(protocol='websocket', port_expose=12345).add(uses=FooExecutor)
with f:
    client = Client(port=12345, protocol='websocket')
    response = client.post(on='/')
    print(response[0].data.docs.texts)
```

````

## Configure the API
The `Flow` API can expose different endpoints depending on the configured Executors. Endpoints are defined by the Executor methods annotated with the `@requests(on='/endpoint_path'')` decorator.

```python
from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests

class EndpointExecutor(Executor):

    @requests(on='/foo')
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was called'))
        
    @requests(on='/bar')
    def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='bar was called'))

f = Flow(protocol='grpc', port_expose=12345).add(uses=EndpointExecutor)
with f:
    client = Client(port=12345)
    foo_response = client.post(on='/foo')
    bar_response = client.post(on='/bar')
    print(foo_response[0].data.docs.texts)
    print(bar_response[0].data.docs.texts)
```

This will print

```text
['foo was called']
['bar was called']
```

The `Client` also offers the convenience functions `.search()` and  `.index()`, which are just shortcuts for `.post(on='/search')` and `.post(on='/index')`.

### Limiting outstanding requests
By default, a Client will just send requests as fast as possible without any throttling. This can potentially put a lot of load on the `Flow` if the Client can send requests faster than they are processed in the `Flow`. Typically, this is most likely to happen for expensive index Flows. 

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

### Extend HTTP Interface

By default the following endpoints are exposed to the public by the API:

| Endpoint  | Description                                         |
| --------- | --------------------------------------------------- |
| `/status` | Check Jina service running status                   |
| `/post`   | Corresponds to `f.post()` method in Python          |
| `/index`  | Corresponds to `f.post('/index')` method in Python  |
| `/search` | Corresponds to `f.post('/search')` method in Python |
| `/update` | Corresponds to `f.post('/update')` method in Python |
| `/delete` | Corresponds to `f.post('/delete')` method in Python |

#### Hide CRUD and debug endpoints from HTTP interface

It is possible to hide CRUD and debug endpoints in production. This might be useful when the context is not applicable. For example, in the code snippet below, we didn't implement any CRUD endpoints for the executor, hence it does not make sense to expose them to public.

```python
from jina import Flow
f = Flow(protocol='http',
         no_debug_endpoints=True,
         no_crud_endpoints=True)
```

```{figure} ../../../.github/2.0/hide-crud-debug-endpoints.png
:align: center
```

#### Expose customized endpoints to HTTP interface

`Flow.expose_endpoint` can be used to expose executor's endpoint to HTTP interface, e.g.

```{figure} ../../../.github/2.0/expose-endpoints.svg
:align: center
```

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

```{figure} ../../../.github/2.0/customized-foo-endpoint.png
:align: center
```

Now, sending HTTP data request to `/foo` is equivalent as calling `f.post('/foo', ...)` in Python.

You can add more kwargs to build richer semantics on your HTTP endpoint. Those meta information will be rendered by Swagger UI and be forwarded to the OpenAPI schema.

```python
f.expose_endpoint('/bar',
                  summary='my endpoint',
                  tags=['fine-tuning'],
                  methods=['PUT']
                  )
```

You can enable custom endpoints in a Flow using yaml syntax as well.

```yaml
jtype: Flow
with:
  protocol: http
  expose_endpoints:
    /foo:
      methods: ["GET"]
    /bar:
      methods: ["PUT"]
      summary: my endpoint
      tags:
        - fine-tuning
    /foobar: {}
executors:
  - name: indexer
```

```{figure} ../../../.github/2.0/rich-openapi.png
:align: center
```

## Working with the Python Client
The most convenient way to work with the `Flow` API is the Python Client. It enables you to send `Documents` to the `Flow` API in a number of different ways shown below:
```python
from docarray import Document, DocumentArray
from jina import Client, Flow

d1 = Document(content='hello')
d2 = Document(content='world')

def doc_gen():
    for j in range(10):
        yield Document(content=f'hello {j}')

with Flow() as f:
    client = Client(port=12345)
    client.post('/endpoint', d1)  # Single document

    client.post('/endpoint', [d1, d2])  # a list of Document

    client.post('/endpoint', doc_gen)  # Document generator

    client.post('/endpoint', DocumentArray([d1, d2]))  # DocumentArray

    client.post('/endpoint')  # empty
```

Especially during indexing a Client often sends thousands of Documents to a `Flow`. Those Documents are internally batched into a `Request`. The size of these batches can be controlled with the `request_size` keyword. The default `request_size` is 100 `Documents`. The optimal size will depend on your use case.
```python
from docarray import Document, DocumentArray
from jina import Flow

with Flow() as f:
    f.post('/', DocumentArray(Document() for _ in range(100)), request_size=10)
```

### Target a specific Executor
Usually a `Flow` will send each request to all Executors with matching Endpoints as configured. But the `Client` also allows you to only target a specific Executor in a `Flow` using the `target_executor` keyword. The request will then only be processed by the Executor with the provided name. Its usage is shown in the listing below.

```python
from docarray import Document, DocumentArray
from jina import Client, Executor, Flow, requests

class FooExecutor(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'foo was here and got {len(docs)} document'))

class BarExecutor(Executor):

    @requests
    def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'bar was here and got {len(docs)} document'))

f = Flow() \
    .add(uses=FooExecutor, name='fooExecutor') \
    .add(uses=BarExecutor, name='barExecutor')

with f:  # Using it as a Context Manager will start the Flow
    client = Client(port=f.port_expose)
    response = client.post(on='/', target_executor='barExecutor')
    print(response[0].data.docs.texts)
```

### Request parameters

The Client can also send parameters to the Executors as shown below:

```{code-block} python
---
emphasize-lines: 14
---
from docarray import Document
from jina import Executor, Flow, requests

class MyExecutor(Executor):

    @requests
    def foo(self, parameters, **kwargs):
        print(parameters['hello'])

f = Flow().add(uses=MyExecutor)

with f:
    f.post('/', Document(), parameters={'hello': 'world'})
```

````{admonition} Note
:class: note
You can send a parameters-only data request via:

```python
with f:
    f.post('/', parameters={'hello': 'world'})
```

This might be useful to control `Executor` objects during their lifetime.
````

### Async Python Client

There is also an async version of the Python Client so that it can easily be used from `asyncio` context:

```python
import asyncio

from docarray import Document
from jina import Client, Flow

async def async_inputs():
    for _ in range(10):
        yield Document()
        await asyncio.sleep(0.1)

async def run_client(port):
    client = Client(port=port, asyncio=True)
    async for resp in client.post('/', async_inputs, request_size=1):
        print(resp)

with Flow() as f:  # Using it as a Context Manager will start the Flow
    asyncio.run(run_client(f.port_expose))
```

## Deployment
To deploy a `Flow` you will need to deploy the Executors it is composed of. The `Flow` is offering convenience functions to generate the necessary configuration files for some use cases. At the moment `Docker-Compose` and `Kubernetes` are supprted.

```python
from jina import Flow

with Flow() as f:
    f.to_docker_compose_yaml()
```
This will generate a single `docker-compose.yml` file containing all the `Executors` of the `Flow`. More in depth information can be found in {ref}`this How-TO <kubernetes>`.

```python
from jina import Flow

with Flow() as f:
    f.to_k8s_yaml('flow_k8s_configuration')
```
This will generate the necessary Kubernetes configuration files for all the `Executors` of the `Flow`. The generated folder can be used directly with `kubectl` to deploy the `Flow` to an existing Kubernetes cluster.
More in depth information can be found in {ref}`this How-TO <docker-compos>`.

