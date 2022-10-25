(client)=
# Client
{class}`~jina.Client` enables you to send Documents to a running {class}`~jina.Flow` in a number of different ways, as shown below.

Clients support four different networking protocols: **HTTP**, **gRPC**, **WebSocket** and **GraphQL**

For each of them, you first connect your Client to the API Gateway, before you can send requests to it.

```{hint}
If you want to connect to your Flow from a programming language other than Python, please follow the third party 
client {ref}`documentation <third-party-client>`.
```


## Connect

If there is not already a Flow running in the background or on the network, you can start one:

```python
from jina import Flow

PORT = 1234
PROTOCOL = 'grpc'  # one of 'grpc', 'http', 'websocket'

with Flow(port=PORT, protocol=PROTOCOL) as f:
    f.block()
```

To connect to the `Flow`, the Client has to specify the followings parameters.
All af these have to match the Flow and how it was set up:
* the `protocol` it needs to use to communicate with the Flow
* the `host` and the `port` as exposed by the Flow
* if it needs to use `TLS` encryption

    
````{Hint} Default port
The default port for the Client is `80` unless you are using `TLS` encryption it will be `443`
````


You can define these parameters by passing a valid URI scheme as part of the `host` argument:

````{tab} TLS disabled

```python
from jina import Client

Client(host='http://my.awesome.flow:1234')
Client(host='ws://my.awesome.flow:1234')
Client(host='grpc://my.awesome.flow:1234')
```

````

````{tab} TLS enabled

```python
from jina import Client

Client(host='https://my.awesome.flow:1234')
Client(host='wss://my.awesome.flow:1234')
Client(host='grpcs://my.awesome.flow:1234')
```

````


Equivalently, you can pass each relevant parameter as a keyword argument:

````{tab} TLS disabled

```python
Client(host='my.awesome.flow', port=1234, protocol='http')
Client(host='my.awesome.flow', port=1234, protocol='websocket')
Client(host='my.awesome.flow', port=1234, protocol='grpc')
```

````

````{tab} TLS enabled

```python
Client(host='my.awesome.flow', port=1234, protocol='http', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='websocket', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='grpc', tls=True)
```

````


You can also use a mixe of both:

```python
Client(host='https://my.awesome.flow', port=1234)
Client(host='my.awesome.flow:1234', protocol='http', tls=True)
```

````{admonition} Caution
:class: caution
You can't define these parameters both by keyword argument and by host scheme - you can't have two sources of truth.
Example: the following code will raise an exception:
```python
Client(host='https://my.awesome.flow:1234', port=4321)
```
````

````{admonition} Hint
:class: hint
The arguments above have usefule defaults: `protocol='grpc'` and `host='0.0.0.0'`.
This is particularly useful when debugging or accessing a Flow on your local machine.

To connect to a Flow `f` it is therefore often enough to do the following:

```{code-block} python
c = Client(port=f.port)
```
````

## Profiling the network

Before sending any real data, you can test the connectivity and network latency by calling the {meth}`~jina.Client.profiling` method:

```python
from jina import Client

c = Client(host='grpc://my.awesome.flow:1234')
c.profiling()
```

```text
 Roundtrip  24ms  100% 
├──  Client-server network  17ms  71% 
└──  Server  7ms  29% 
    ├──  Gateway-executors network  0ms  0% 
    ├──  executor0  5ms  71% 
    └──  executor1  2ms  29% 
```

## Send data

After a {class}`~jina.Client` has connected to a {class}`~jina.Flow`, it can send requests to the Flow using its {meth}`~jina.clients.mixin.PostMixin.post` method.
This expects as inputs the {ref}`Executor endpoint <exec-endpoint>` that you want to target, as well as a Document or Iterable of Documents:


```python
from docarray import Document, DocumentArray


d1 = Document(content='hello')
d2 = Document(content='world')


def doc_gen():
    for j in range(10):
        yield Document(content=f'hello {j}')


client = Client(port=PORT)

client.post('/endpoint', d1)  # Single Document

client.post('/endpoint', [d1, d2])  # List of Documents

client.post('/endpoint', doc_gen)  # Document generator

client.post('/endpoint', DocumentArray([d1, d2]))  # DocumentArray

client.post('/endpoint')  # Empty
```


```{admonition} Caution
:class: caution
`Flow` also provides a `.post()` method that follows the same interface as `client.post()`.
However, once your solution is deployed remotely, the Flow interface is not present anymore.
Hence, `flow.post()` is not recommended outside of testing or debugging use cases.
```

## Send parameters

The {class}`~jina.Client` can also send parameters to the {class}`~jina.Executor`s as shown below:

```{code-block} python
---
emphasize-lines: 14
---

from jina import Client, Executor, Flow, requests, Document

class MyExecutor(Executor):

    @requests
    def foo(self, parameters, **kwargs):
        print(parameters['hello'])

f = Flow().add(uses=MyExecutor)

with f:
    client = Client(port=f.port)
    client.post('/', Document(), parameters={'hello': 'world'})
```

````{hint} 
:class: note
You can send a parameters-only data request via:

```python
with f:
    client = Client(port=f.port)
    client.post('/', parameters={'hello': 'world'})
```

This might be useful to control `Executor` objects during their lifetime.
````

(specific-params)=
### Send parameters to specific Executors

You can send parameters to specific Executor by using the `executor__parameter` syntax.
The Executor named `executorname` will receive the parameter `paramname` (without the `executorname__` in the key name) 
and none of the other Executors will receive it.

For instance in the following Flow:

```python
from jina import Flow, DocumentArray

with Flow().add(name='exec1').add(name='exec2') as flow:

    flow.index(
        DocumentArray.empty(size=5),
        parameters={'exec1__traversal_path': '@r', 'exec2__traversal_path': '@c'},
    )
```

The Executor `exec1` will receive `{'traversal_path':'@r'}` as parameters, whereas `exec2` will receive `{'traversal_path':'@c'}` as parameters.

This feature is intended for the case where there are multiple Executors that take the same parameter names, but you want to use different values for each Executor.
This is often the case for Executors from the Hub, since they tend to share a common interface for parameters.



## Async send

There also exists an async version of the Python Client which works with {meth}`~jina.clients.mixin.PostMixin.post` and {meth}`~jina.clients.mixin.MutateMixin.mutate`.

While the standard `Client` is also asynchronous under the hood, its async version exposes this fact to the outside world,
by allowing *coroutines* as input, and returning an *asynchronous iterator*.
This means you can iterate over Responses one by one, as they come in.

```python
import asyncio

from jina import Client, Flow, Document


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

Async send is useful when calling a Flow from an Executor, as described in {ref}`async-executors`.

```python
from jina import Client, Executor, requests, DocumentArray


class DummyExecutor(Executor):

    c = Client(host='grpc://0.0.0.0:51234', asyncio=True)

    @requests
    async def process(self, docs: DocumentArray, **kwargs):
        self.c.post('/', docs)
```


## Batch data

Especially during indexing, a Client can send up to thousands or millions of Documents to a {class}`~jina.Flow`.
Those Documents are internally batched into a `Request`, providing a smaller memory footprint and faster response times thanks
to {ref}`callback functions <callback-functions>`.

The size of these batches can be controlled with the `request_size` keyword.
The default `request_size` is 100 Documents. The optimal size will depend on your use case.
```python
from jina import Flow, Client, Document, DocumentArray

with Flow() as f:
    client = Client(port=f.port)
    client.post('/', DocumentArray(Document() for _ in range(100)), request_size=10)
```

## Bypass Executor

Usually a {class}`~jina.Flow` will send each request to all {class}`~jina.Executor`s with matching endpoints as configured. But the {class}`~jina.Client` also allows you to only target specific Executors in a Flow using the `target_executor` keyword. The request will then only be processed by the Executors which match the provided target_executor regex. Its usage is shown in the listing below.

```python
from jina import Client, Executor, Flow, requests, Document, DocumentArray


class FooExecutor(Executor):
    @requests
    async def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'foo was here and got {len(docs)} document'))


class BarExecutor(Executor):
    @requests
    async def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'bar was here and got {len(docs)} document'))


f = (
    Flow()
    .add(uses=FooExecutor, name='fooExecutor')
    .add(uses=BarExecutor, name='barExecutor')
)

with f:  # Using it as a Context Manager will start the Flow
    client = Client(port=f.port)
    docs = client.post(on='/', target_executor='bar*')
    print(docs.texts)
```
This will send the request to all Executors whose names start with 'bar', such as 'barExecutor'.
In the simplest case, you can specify a precise Executor name, and the request will be sent only to that single Executor.

(callback-functions)=
## Callbacks

After performing {meth}`~jina.clients.mixin.PostMixin.post`, you may want to further process the obtained results.

For this purpose, Jina implements a promise-like interface, letting you specify three kinds of callback functions:

- `on_done` is executed while streaming, after successful completion of each request
- `on_error` is executed while streaming, whenever an error occurs in each request
- `on_always` is always performed while streaming, no matter the success or failure of each request


Note that these callbacks only work for requests (and failures) *inside the stream*, for example inside an Executor.
If the failure is due to an error happening outside of 
streaming, then these callbacks will not be triggered.
For example, a `SIGKILL` from the client OS during the handling of the request, or a networking issue,
will not trigger the callback.



Callback functions in Jina expect a `Response` of the type {class}`~jina.types.request.data.DataRequest`, which contains resulting Documents,
parameters, and other information.


````{hint} Understanding DataRequest

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
from jina import Flow, Client, Document


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



## Returns

`client.post()` returns a flattened `DocumentArray` containing all Documents of all Requests.

By setting `return_responses=True` as an argument to `client.post(return_responses=True)`, this behavior can be modified to return a list of Responses
(`DataRequest`s) instead.

If a callback is provided, no results will be returned.

```{caution}
Not using a callback function and instead returning results can come with a **serious performance penalty**.

Callbacks operate on each individual Request, which represents a batch of the data.
In contrast, returning results requires the accumulation of all results of all Requests.
This means that you will not receive results until all Requests have been processed.
This may not only be slower, but also require more memory.
```

````{tab} Returning DocumentArray

```python
from jina import Flow, Client, Document

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
from jina import Flow, Client, Document

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
from jina import Flow, Client, Document

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

(client-compress)=
## Enable compression

If the communication to the Gateway is via gRPC, you can pass `compression` parameter to  {meth}`~jina.clients.mixin.PostMixin.post` to benefit from [gRPC compression](https://grpc.github.io/grpc/python/grpc.html#compression) methods. 

The supported choices are: None, `gzip` and `deflate`.

```python
from jina import Client

client = Client()
client.post(..., compression='Gzip')
```

Note that this setting is only effective the communication between the client and the Flow's gateway.

One can also specify the compression of the internal communication {ref}`as described here<serve-compress>`.


## Enable TLS

To connect to a {class}`~jina.Flow` that has been {ref}`configured to use TLS <flow-tls>` in combination with gRPC, http, or websocket,
set the Client's `tls` parameter to `True`:

```python
c_http = Client(protocol='http', tls=True, host=..., port=...)
c_ws = Client(protocol='websocket', tls=True, host=..., port=...)
c_grpc = Client(protocol='grpc', tls=True, host=..., port=...)
```

The same can be achieved by passing a valid URI to the `host` parameter, and appending 's' to the protocol definition:

```python
Client(host='https://my.awesome.flow:1234')
Client(host='wss://my.awesome.flow:1234')
Client(host='grpcs://my.awesome.flow:1234')
```

## Use GraphQL

The Jina {class}`~jina.Client` additionally supports fetching data via GraphQL mutations using {meth}`~jina.clients.mixin.MutateMixin.mutate`:

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

```{toctree}
:hidden:

third-party-client
```