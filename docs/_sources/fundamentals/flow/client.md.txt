(client)=
# Client API
The most convenient way to work with the `Flow` API is the Python Client.
It enables you to send `Documents` to a running `Flow` in a number of different ways, as shown below.

```{admonition} Caution
:class: caution
`Flow` provides a `.post()` method that follows the same interface as `client.post()`.
However, once your solution is deployed in the cloud, the Flow interface is not present anymore.
Hence, `flow.post()` is not recommended outside of testing or debugging use cases.
```

## HTTP, gRPC, and WebSocket

Jina Flows and Clients support three different networking protocols: HTTP, gRPC, and WebSocket.
These can all be used in the same way by using `client.post()`.

Starting the Flow:

```python
from jina import Flow

PORT = 12345
PROTOCOL = 'grpc'  # one of 'grpc', 'http', 'websocket'

with Flow(port=PORT, protocol=PROTOCOL) as f:
    f.block()
```

To connect a Client to the Flow's gateway, you need to specify an IP host address and port on which the Flow can be reached.
This is done using the `host=` and `port=` constructor keywords.
If the Client and the Flow gateway are running on the same machine, the `host=` parameter can be omitted, as it defaults to `'0.0.0.0'`.

Additionally, the connection protocol can be toggled between `'grpc'`, `'http'`, and `'websocket'` using the `protocol=`
keyword, where `'grpc'` is the default.

```python
from jina import Client

HOST = '0.0.0.0'  # host address where the Flow can be reached
PORT = 12345  # port where the Flow can be reached
PROTOCOL = 'grpc'  # one of 'grpc', 'http', 'websocket'. Needs to be same as specified by the Flow

client = Client(host=HOST, port=PORT, protocol=PROTOCOL)
```

Then, the Client can send requests to the Flow using its `.post()` method.
This expects as inputs the {ref}`Executor endpoint <exec-endpoint>` that you want to target, as well as a Document or Iterable of Documents:


```python
from docarray import Document, DocumentArray


d1 = Document(content='hello')
d2 = Document(content='world')


def doc_gen():
    for j in range(10):
        yield Document(content=f'hello {j}')


client = Client(host=HOST, port=PORT)

client.post('/endpoint', d1)  # Single Document

client.post('/endpoint', [d1, d2])  # List of Documents

client.post('/endpoint', doc_gen)  # Document generator

client.post('/endpoint', DocumentArray([d1, d2]))  # DocumentArray

client.post('/endpoint')  # Empty
```
### Specifying Host scheme

To connect to the `Flow` the client has to specify the followings parameters:
* the `protocol` it needs to use to communicate with the `Flow
* the `host` and the `port`on which the Flow is exposed
* if he needs to use `tls` encryption

You can define these parameters by passing a valid URI scheme as part of the `host` argument:

```python
from jina import Client

Client(host='https://my.awesome.flow:1234')
Client(host='wss://my.awesome.flow:1234')
Client(host='grpcs://my.awesome.flow:1234')
```

You can as well pass each relevant parameter as a keyword argument:

the following example is equivalent to the one above
```python
Client(host='my.awesome.flow', port=1234, protocol='http', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='websocket', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='grpc', tls=True)
```

You can use a mixe of both as well:

```python
Client(host='https://my.awesome.flow', port=1234)
Client(host='my.awesome.flow:1234', protocol='http', tls=True)
```

````{admonition} Caution
:class: caution
You can't define these parameters by keyword arugment and by host scheme (You can't have two sources of truth)
Example : the following code will raise an exception
```python
Client(host='https://my.awesome.flow:1234', port=4321)
```
````






### Batching Requests

Especially during indexing, a Client can send up to thousands or millions of Documents to a `Flow`.
Those Documents are internally batched into a `Request`, providing a smaller memory footprint and faster response times thanks
to {ref}`callback functions <callback-functions>`.

The size of these batches can be controlled with the `request_size` keyword.
The default `request_size` is 100 `Documents`. The optimal size will depend on your use case.
```python
from docarray import Document, DocumentArray
from jina import Flow, Client

with Flow() as f:
    client = Client(port=f.port)
    client.post('/', DocumentArray(Document() for _ in range(100)), request_size=10)
```

### Targeting a specific Executor
Usually a `Flow` will send each request to all Executors with matching endpoints as configured. But the `Client` also allows you to only target a specific Executor in a `Flow` using the `target_executor` keyword. The request will then only be processed by the Executor with the provided name. Its usage is shown in the listing below.

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


f = (
    Flow()
    .add(uses=FooExecutor, name='fooExecutor')
    .add(uses=BarExecutor, name='barExecutor')
)

with f:  # Using it as a Context Manager will start the Flow
    client = Client(port=f.port)
    docs = client.post(on='/', target_executor='barExecutor')
    print(docs.texts)
```

### Request parameters

The Client can also send parameters to the Executors as shown below:

```{code-block} python
---
emphasize-lines: 14
---
from docarray import Document
from jina import Client, Executor, Flow, requests

class MyExecutor(Executor):

    @requests
    def foo(self, parameters, **kwargs):
        print(parameters['hello'])

f = Flow().add(uses=MyExecutor)

with f:
    client = Client(port=f.port)
    client.post('/', Document(), parameters={'hello': 'world'})
```

````{admonition} Note
:class: note
You can send a parameters-only data request via:

```python
with f:
    client = Client(port=f.port)
    client.post('/', parameters={'hello': 'world'})
```

This might be useful to control `Executor` objects during their lifetime.
````

(callback-functions)=
### Processing results using callback functions

After performing `client.post()`, you may want to further process the obtained results.

For this purpose, Jina implements a promise-like interface, letting you specify three kinds of callback functions:

- `on_done` is executed after successful completion of `client.post()`
- `on_error` is executed whenever an error occurs in `client.post()`
- `on_always` is always performed, no matter the success or failure of `client.post()`

```{admonition} Tip
:class: tip
Both `on_done`and `on_always` callback won't be trigger if the failure is due to an error happening outside of 
networking or internal jina issues. For example, if a `SIGKILL` is triggered by the OS during the handling of the request
none of the callback will be executed.   
```



Callback functions in Jina expect a `Response` of the type `jina.types.request.data.DataRequest`, which contains resulting Documents,
parameters, and other information.


````{admonition} Understanding DataRequest
:class: note

`DataRequest`s are objects that are sent by Jina internally. Callback functions process DataRequests, and `client.post()`
can return DataRequests.

`DataRequest` objects can be seen as a container for data relevant for a given request, most importantly:

- `dr.docs`: The DocumentArray being passed between and returned by the Executors.
    These are the Documents usually processed in a callback function, and are often the main payload.
- `dr.parameters`: The input parameters of the associated request.
    - `dr.parameters['__results__']`: Reserved field that gets populated by Executors returning a Python `dict`.
        Information in those returned `dict`s gets collected here, behind each Executor's *pod_id*.
- `dr.data`: Contains information associated with the data in the request. Most importatnly, `dr.data.docs` refers to the
    same object as `dr.docs`.

````

Accordingly, a callback function can be defined in the following way:

````{tab} General callback function

```python
from jina.types.request.data import DataRequest


def my_callback(resp: DataRequest):
    ...  # process request here
```

````
````{tab} Processing documents

```python
from jina.types.request.data import DataRequest


def my_callback(resp: DataRequest):
    docs = resp.docs
    ...  # process docs here
```

````

In the example below, our Flow passes the message then prints the result when successful.
If something goes wrong, it beeps. Finally, the result is written to output.txt.

```python
from jina import Flow, Client
from docarray import Document


def beep(*args):
    # make a beep sound
    import sys

    sys.stdout.write('\a')


with Flow().add() as f, open('output.txt', 'w') as fp:
    client = Client(port=f.port)
    client.post(
        '/',
        Document(),
        on_done=print,
        on_error=beep,
        on_always=lambda x: x.docs.save(fp),
    )
```
### On failure callback

Additionally, the `on_error` callback can be triggered by a raise of an exception. The callback must take an optional 
`exception` parameters as an argument.

```python
def on_error(resp, exception: Exception):
    ...
```

### Returning results from .post()

If no callback is provided, `client.post()` returns a flattened `DocumentArray` containing all Documents of all Requests.

By setting `return_responses=True` as an argument to `client.post(return_responses=True), this behavior can be modified to return a list of Responses
(`DataRequest`s) instead.

If a callback is provided, no results will be returned.

```{admonition} Danger
:class: danger
Not using a callback function and instead returning results can come with a **serious performance penalty**.

Callbacks operate on each individual Request, which represents a batch of the data.
In contrast, returning results requires the accumulation of all results of all Requests.
This means that you will not receive results until all Requests have been processed.
This may not only be slower, but also require more memory.
```

````{tab} Returning DocumentArray

```python
from jina import Flow, Client
from docarray import Document

with Flow() as f:
    client = Client(port=f.port)
    docs = client.post(on='', inputs=Document(text='Hi there!'))
    print(docs)
    print(docs.texts)
```
```  
>>> <DocumentArray (length=1) at 140619524357664>
>>> ['Hi there!']
```

````
````{tab} Returning Responses

```python
from jina import Flow, Client
from docarray import Document

with Flow() as f:
    client = Client(port=f.port)
    resp = client.post(on='', inputs=Document(text='Hi there!'), return_responses=True)
    print(resp)
    print(resp[0].docs.texts)
```
``` 
>>> [<jina.types.request.data.DataRequest ('header', 'parameters', 'routes', 'data') at 140619524354592>]
>>> ['Hi there!']
```

````
````{tab} Using callback function

```python
from jina import Flow, Client
from docarray import Document

with Flow() as f:
    client = Client(port=f.port)
    resp = client.post(
        on='',
        inputs=Document(text='Hi there!'),
        on_done=lambda resp: print(resp.docs.texts),
    )
    print(resp)
```
```
>>> ['Hi there!']
>>> None
```

````

### Custom gRPC compression for GRPC Client

If the communication to the `Flow` needs to be done via gRPC, you can pass `compression` parameter to `client.post` to benefit from (`grpc compression`)[https://grpc.github.io/grpc/python/grpc.html#compression] methods. 
The supported methods are: `NoCompression`, `Gzip` and `Deflate`.

```python
from jina import Client

client = Client()
client.post(..., compression='Gzip')
```

## GraphQL

The Jina Client additionally supports fetching data via GraphQL mutations using `client.mutate()`:

```python
from jina import Client

PORT = ...
c = Client(port=PORT)
mut = '''
        mutation {
            docs(data: {text: "abcd"}) { 
                id
                matches {
                    embedding
                }
            } 
        }
    '''
response = c.mutate(mutation=mut)
```

For details on the allowed mutation arguments and response fields, see {ref}`here <flow-graphql>`.

## Async Python Client

There also exists an async version of the Python Client which works with `.post()` and `.mutate()`.

While the standard `Client` is also asynchronous under the hood, its async version exposes this fact to the outside world,
by allowing *coroutines* as input, and returning an *asynchronous iterator*.
This means you can iterate over Responses one by one, as they come in.

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
    asyncio.run(run_client(f.port))
```
