# Send & Receive Data

After a {class}`~jina.Client` has connected to a {class}`~jina.Deployment` or a {class}`~jina.Flow`, it can send requests to the service using its
{meth}`~jina.clients.mixin.PostMixin.post` method.
This expects as inputs the {ref}`Executor endpoint <exec-endpoint>` that you want to target, as well as a Document or
Iterable of Documents:

````{tab} A single Document

```{code-block} python
---
emphasize-lines: 6
---
from docarray.documents import TextDoc

d1 = TextDoc(text='hello')
client = Client(...)

client.post('/endpoint', d1)
```

````

````{tab} A list of Documents

```{code-block} python
---
emphasize-lines: 7
---
from docarray.documents import TextDoc

d1 = TextDoc(text='hello')
d2 = TextDoc(text='world')
client = Client(...)

client.post('/endpoint', inputs=[d1, d2])
```

````

````{tab} A DocList

```{code-block} python
---
emphasize-lines: 6
---
from docarray import DocList

d1 = TextDoc(text='hello')
d2 = TextDoc(text='world')
da = DocList[TextDoc]([d1, d2])
client = Client(...)

client.post('/endpoint', da)
```

````

````{tab} A Generator of Document

```{code-block} python
---
emphasize-lines: 3-5, 9
---
from docarray.documents import TextDoc

def doc_gen():
    for j in range(10):
        yield TextDoc(content=f'hello {j}')
        
client = Client(...)

client.post('/endpoint', doc_gen)
```

````

````{tab} No Document

```{code-block} python
---
emphasize-lines: 3
---
client = Client(...)

client.post('/endpoint')
```

````

```{admonition} Caution
:class: caution
`Flow` and `Deployment` also provides a `.post()` method that follows the same interface as `client.post()`.
However, once your solution is deployed remotely, these objects are not present anymore.
Hence, `deployment.post()` and `flow.post()` is not recommended outside of testing or debugging use cases.
```

(request-size-client)=
## Send data in batches

Especially during indexing, a Client can send up to thousands or millions of Documents to a {class}`~jina.Flow`.
Those Documents are internally batched into a `Request`, providing a smaller memory footprint and faster response times
thanks
to {ref}`callback functions <callback-functions>`.

The size of these batches can be controlled with the `request_size` keyword.
The default `request_size` is 100 Documents. The optimal size will depend on your use case.

```python
from jina import Deployment, Client
from docarray import DocList, BaseDoc

with Deployment() as dep:
    client = Client(port=f.port)
    client.post('/', DocList[BaseDoc](BaseDoc() for _ in range(100)), request_size=10)
```

## Send data asynchronously

There is an async version of the Python Client which works with {meth}`~jina.clients.mixin.PostMixin.post` and
{meth}`~jina.clients.mixin.MutateMixin.mutate`.

While the standard `Client` is also asynchronous under the hood, its async version exposes this fact to the outside
world,
by allowing *coroutines* as input, and returning an *asynchronous iterator*.
This means you can iterate over Responses one by one, as they come in.

```python
import asyncio

from jina import Client, Deployment
from docarray import BaseDoc


async def async_inputs():
    for _ in range(10):
        yield BaseDoc()
        await asyncio.sleep(0.1)


async def run_client(port):
    client = Client(port=port, asyncio=True)
    async for resp in client.post('/', async_inputs, request_size=1):
        print(resp)


with Deployment() as dep:  # Using it as a Context Manager will start the Deployment
    asyncio.run(run_client(dep.port))
```

Async send is useful when calling an external service from an Executor.

```python
from jina import Client, Executor, requests
from docarray import DocList, BaseDoc


class DummyExecutor(Executor):
    c = Client(host='grpc://0.0.0.0:51234', asyncio=True)

    @requests
    async def process(self, docs: DocList[BaseDoc], **kwargs) -> DocList[BaseDoc]:
        return self.c.post('/', docs, return_type=DocList[BaseDoc])
```

## Send data to specific Executors

Usually a {class}`~jina.Flow` will send each request to all {class}`~jina.Executor`s with matching endpoints as
configured. But the {class}`~jina.Client` also allows you to only target specific Executors in a Flow using
the `target_executor` keyword. The request will then only be processed by the Executors which match the provided
target_executor regex. Its usage is shown in the listing below.

```python
from jina import Client, Executor, Flow, requests
from docarray import DocList
from docarray.documents import TextDoc


class FooExecutor(Executor):
    @requests
    async def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = f'foo was here and got {len(docs)} document'

class BarExecutor(Executor):
    @requests
    async def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = f'bar was here and got {len(docs)} document'


f = (
    Flow()
        .add(uses=FooExecutor, name='fooExecutor')
        .add(uses=BarExecutor, name='barExecutor')
)

with f:  # Using it as a Context Manager will start the Flow
    client = Client(port=f.port)
    docs = client.post(on='/', inputs=TextDoc(text=''), target_executor='bar*', return_type=DocList[TextDoc])
    print(docs.text)
```

This will send the request to all Executors whose names start with 'bar', such as 'barExecutor'.
In the simplest case, you can specify a precise Executor name, and the request will be sent only to that single
Executor.

## Use Unary or Streaming gRPC

The Flow with **gRPC** protocol implements the unary and the streaming RPC lifecycle for communicating with the clients.
When sending more than one request using the batching or the iterator mechanism, the RPC lifecycle for the
{meth}`~jina.clients.mixin.PostMixin.post` method can be controlled using the `stream` boolean method argument. By
default the stream option is set to `True` which uses the streaming RPC to send the data to the Flow. If the stream
option is set to `False`, the unary RPC is used to send the data to the Flow.
Both RPC lifecycles are implemented to provide the flexibility for the clients.

There might be performance penalties when using the streaming RPC in the Python gRPC implementation.

```{hint}
This option is only valid for **gRPC** protocol.

Refer to the gRPC [Performance Best Practices](https://grpc.io/docs/guides/performance/#general) guide for more implementations details and considerations.
```

(client-grpc-channel-options)=

## Configure gRPC Client options

The `Client` supports the `grpc_channel_options` parameter which allows more customization of the **gRPC** channel
construction. The `grpc_channel_options` parameter accepts a dictionary of **gRPC** configuration options which will be
used to overwrite the default options. The default **gRPC** options are:

```
('grpc.max_send_message_length', -1),
('grpc.max_receive_message_length', -1),
('grpc.keepalive_time_ms', 9999),
# send keepalive ping every 9 second, default is 2 hours.
('grpc.keepalive_timeout_ms', 4999),
# keepalive ping time out after 4 seconds, default is 20 seconds
('grpc.keepalive_permit_without_calls', True),
# allow keepalive pings when there's no gRPC calls
('grpc.http1.max_pings_without_data', 0),
# allow unlimited amount of keepalive pings without data
('grpc.http1.min_time_between_pings_ms', 10000),
# allow grpc pings from client every 9 seconds
('grpc.http1.min_ping_interval_without_data_ms', 5000),
# allow grpc pings from client without data every 4 seconds
```

If the `max_attempts` is greater than 1 on the {meth}`~jina.clients.mixin.PostMixin.post` method,
the `grpc.service_config` option will not be applied since the retry
options will be configured internally.

Refer to the [channel_arguments](https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments) section for
the full list of available **gRPC** options.

```{hint}
:class: seealso
Refer to the {ref}`Configure Executor gRPC options <executor-grpc-server-options>` section for configuring the `Executor` **gRPC** options.
```

## Returns

TODO(Joan): Clarify what happens when return_type is singleton and the Result has only a single Document

{meth}`~jina.clients.mixin.PostMixin.post` returns a `DocList` containing all Documents flattened over all
Requests. When setting `return_responses=True`, this behavior is changed to returning a list of
{class}`~jina.types.request.data.Response` objects.

If a callback function is provided, `client.post()` will return none.

````{tab} Return as DocList objects

```python
from jina import Deployment, Client
from docarray import DocList
from docarray.documents import TextDoc

with Deployment() as dep:
    client = Client(port=dep.port)
    docs = client.post(on='', inputs=TextDoc(text='Hi there!'), return_type=DocList[TextDoc])
    print(docs)
    print(docs.text)
```
```console  
<DocList[TextDoc] (length=1)>
['Hi there!']
```

````

````{tab} Return as Response objects

```python
from docarray import DocList
from docarray.documents import TextDoc

with Deployment() as dep:
    client = Client(port=dep.port)
    resp = client.post(on='', inputs=TextDoc(text='Hi there!'), return_type=DocList[TextDoc], return_responses=True)
    print(resp)
    print(resp[0].docs.text)
```
```console 
[<jina.types.request.data.DataRequest ('header', 'parameters', 'routes', 'data') at 140619524354592>]
['Hi there!']
```

````

````{tab} Handle response via callback

```python
from jina import Flow, Client
from docarray import DocList
from docarray.documents import TextDoc

with Deployment() as dep:
    client = Client(port=f.port)
    resp = client.post(
        on='',
        inputs=TextDoc(text='Hi there!'),
        on_done=lambda resp: print(resp.docs.texts),
    )
    print(resp)
```
```console
['Hi there!']
None
```

````

### Callbacks vs returns

Callback operates on every sub-request generated by `request_size`. The callback function consumes the response one by
one. The old response is immediately free from the memory after the consumption.

When callback is not provided, the client accumulates all DocLists of all Requests before returning.
This means you will not receive results until all Requests have been processed, which is slower and requires more
memory.

### Force the order of responses

Note that the Flow processes Documents in an asynchronous and a distributed manner. The order of the Flow processing the
requests may not be the same order as the Client sending them. Hence, the response order may also not be consistent as
the sending order.

To force the order of the results to be deterministic and the same as when they are sent, passing `results_in_order`
parameter to {meth}`~jina.clients.mixin.PostMixin.post`.

```python
import random
import time
from jina import Deployment, Executor, requests, Client
from docarray import DocList
from docarray.documents import TextDoc


class RandomSleepExecutor(Executor):
    @requests
    def foo(self, *args, **kwargs):
        rand_sleep = random.uniform(0.1, 1.3)
        time.sleep(rand_sleep)


dep = Deployment(uses=RandomSleepExecutor, replicas=3)
input_text = [f'ordinal-{i}' for i in range(180)]
input_da = DocList[TextDoc]([TextDoc(text=t) for t in input_text])

with f:
    c = Client(port=dep.port, protocol=dep.protocol)
    output_da = c.post('/', inputs=input_da, request_size=10, return_type=DocList[TextDoc], results_in_order=True)
    for input, output in zip(input_da, output_da):
        assert input.text == output.text
```


