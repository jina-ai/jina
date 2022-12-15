(client)=
# Client
{class}`~jina.Client` enables you to send Documents to a running {class}`~jina.Flow`. Same as Gateway, Client supports four networking protocols: **gRPC**, **HTTP**, **WebSocket** and **GraphQL** with/without TLS.

You may have observed two styles of using a Client in the docs:

````{tab} Implicit, inside a Flow

```{code-block} python
---
emphasize-lines: 6
---
from jina import Flow

f = Flow()

with f:
    f.post('/')
```

````

````{tab} Explicit, outside a Flow

```{code-block} python
---
emphasize-lines: 3,4
---
from jina import Client

c = Client(...)  # must match the Flow setup
c.post('/')
```

````

The implicit style is easier in debugging and local development, as you don't need to specify the host, port and protocol of the Flow. However, it makes very strong assumptions on (1) one Flow only corresponds to one client (2) the Flow is running on the same machine as the Client. For those reasons, explicit style is recommended for production use.

```{hint}
If you want to connect to your Flow from a programming language other than Python, please follow the third party 
client {ref}`documentation <third-party-client>`.
```


## Connect

To connect to a Flow started by:

```python
from jina import Flow

with Flow(port=1234, protocol='grpc') as f:
    f.block()
```

```text
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓      Protocol                   GRPC  │
│  🏠        Local           0.0.0.0:1234  │
│  🔒      Private     192.168.1.126:1234  │
│  🌍       Public    87.191.159.105:1234  │
╰──────────────────────────────────────────╯
```

The Client has to specify the followings parameters to match the Flow and how it was set up:
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
from jina import Client

Client(host='my.awesome.flow', port=1234, protocol='http')
Client(host='my.awesome.flow', port=1234, protocol='websocket')
Client(host='my.awesome.flow', port=1234, protocol='grpc')
```

````

````{tab} TLS enabled

```python
from jina import Client

Client(host='my.awesome.flow', port=1234, protocol='http', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='websocket', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='grpc', tls=True)
```

````


You can also use a mix of both:

```python
from jina import Client

Client(host='https://my.awesome.flow', port=1234)
Client(host='my.awesome.flow:1234', protocol='http', tls=True)
```

````{admonition} Caution
:class: caution
You can't define these parameters both by keyword argument and by host scheme - you can't have two sources of truth.
Example: the following code will raise an exception:
```python
from jina import Client

Client(host='https://my.awesome.flow:1234', port=4321)
```
````

````{admonition} Caution
:class: caution
In case you instanciate a `Client` object using the `grpc` protocol, keep in mind that `grpc` clients cannot be used in 
a multi-threaded environment (check [this gRPC issue](https://github.com/grpc/grpc/issues/25364) for reference).
What you should do, is to rely on asynchronous programming or multi-processing rather than multi-threading.
For instance, if you're building a web server, you can introduce multi-processing based parallelism to your app using 
`gunicorn`: `gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker ...`
````



## Test readiness of the Flow

```{include} ../flow/health-check.md
:start-after: <!-- start flow-ready -->
:end-before: <!-- end flow-ready -->
```


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


````{tab} A single Document

```{code-block} python
---
emphasize-lines: 6
---
from docarray import Document

d1 = Document(content='hello')
client = Client(...)

client.post('/endpoint', d1)
```

````

````{tab} A list of Documents

```{code-block} python
---
emphasize-lines: 7
---
from docarray import Document

d1 = Document(content='hello')
d2 = Document(content='world')
client = Client(...)

client.post('/endpoint', [d1, d2])

```

````

````{tab} A DocumentArray

```{code-block} python
---
emphasize-lines: 6
---
from docarray import DocumentArray

da = DocumentArray.empty(10)
client = Client(...)

client.post('/endpoint', da)
```

````

````{tab} A Generator of Document

```{code-block} python
---
emphasize-lines: 3-5, 9
---
from docarray import Document

def doc_gen():
    for j in range(10):
        yield Document(content=f'hello {j}')
        
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
`Flow` also provides a `.post()` method that follows the same interface as `client.post()`.
However, once your solution is deployed remotely, the Flow interface is not present anymore.
Hence, `flow.post()` is not recommended outside of testing or debugging use cases.
```



### Send data asynchronously

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


### Send data in batches

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

### Send data to specific Executor

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
from jina import Flow, DocumentArray, Client

with Flow().add(name='exec1').add(name='exec2') as f:

    client = Client(port=f.port)

    client.post(
        '/index',
        DocumentArray.empty(size=5),
        parameters={'exec1__traversal_path': '@r', 'exec2__traversal_path': '@c'},
    )
```

The Executor `exec1` will receive `{'traversal_path':'@r'}` as parameters, whereas `exec2` will receive `{'traversal_path':'@c'}` as parameters.

This feature is intended for the case where there are multiple Executors that take the same parameter names, but you want to use different values for each Executor.
This is often the case for Executors from the Hub, since they tend to share a common interface for parameters.

```{admonition} Difference to target_executor

Why do we need this feature if we already have `target_executor`?

On the surface, both of them is about sending information to a partial Flow, i.e. a subset of Executors. However, they work differently under the hood. `target_executor` directly send info to those specified executors, ignoring the topology of the Flow; whereas `executor__parameter`'s request follows the topology of the Flow and only send parameters to the Executor that matches.

Think about roll call and passing notes in a classroom. `target_executor` is like calling a student directly, whereas `executor__parameter` is like asking him/her to pass the notes to the next student one by one while each picks out the note with its own name.
```



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

### Handle DataRequest in callbacks

`DataRequest`s are objects that are sent by Jina internally. Callback functions process DataRequests, and `client.post()`
can return DataRequests.

`DataRequest` objects can be seen as a container for data relevant for a given request, it contains the following fields:

````{tab} header

The request header.

```python
from pprint import pprint

from jina import Client

Client().post(on='/', on_done=lambda x: pprint(x.header))
```

```console
request_id: "ea504823e9de415d890a85d1d00ccbe9"
exec_endpoint: "/"
target_executor: ""
```

````

````{tab} parameters

The input parameters of the associated request. In particular, `DataRequest.parameters['__results__']` is a 
reserved field that gets populated by Executors returning a Python `dict`. 
Information in those returned `dict`s gets collected here, behind each Executor ID.

```python
from pprint import pprint

from jina import Client

Client().post(on='/', on_done=lambda x: pprint(x.parameters))
```

```console
{'__results__': {}}
```

````

````{tab} routes

The routing information of the data request. It contains the which Executors have been called, and the order in which they were called.
The timing and latency of each Executor is also recorded.

```python
from pprint import pprint

from jina import Client

Client().post(on='/', on_done=lambda x: pprint(x.routes))
```

```console
[executor: "gateway"
start_time {
  seconds: 1662637747
  nanos: 790248000
}
end_time {
  seconds: 1662637747
  nanos: 794104000
}
, executor: "executor0"
start_time {
  seconds: 1662637747
  nanos: 790466000
}
end_time {
  seconds: 1662637747
  nanos: 793982000
}
]

```

````

````{tab} docs
The DocumentArray being passed between and returned by the Executors. These are the Documents usually processed in a callback function, and are often the main payload.

```python
from pprint import pprint

from jina import Client

Client().post(on='/', on_done=lambda x: pprint(x.docs))
```

```console
<DocumentArray (length=0) at 5044245248>

```
````

  
Accordingly, a callback that processing documents can be defined as:

```{code-block} python
---
emphasize-lines: 4
---
from jina.types.request.data import DataRequest

def my_callback(resp: DataRequest):
    foo(resp.docs)
```

### Handle exceptions in callbacks

Server error can be caught by Client's `on_error` callback function. You can get the error message and traceback from `header.status`:

```python
from pprint import pprint

from jina import Flow, Client, Executor, requests


class MyExec1(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError


with Flow(port=12345).add(uses=MyExec1) as f:
    c = Client(port=f.port)
    c.post(on='/', on_error=lambda x: pprint(x.header.status))
```


```text
code: ERROR
description: "NotImplementedError()"
exception {
  name: "NotImplementedError"
  stacks: "Traceback (most recent call last):\n"
  stacks: "  File \"/Users/hanxiao/Documents/jina/jina/serve/runtimes/worker/__init__.py\", line 181, in process_data\n    result = await self._data_request_handler.handle(requests=requests)\n"
  stacks: "  File \"/Users/hanxiao/Documents/jina/jina/serve/runtimes/request_handlers/data_request_handler.py\", line 152, in handle\n    return_data = await self._executor.__acall__(\n"
  stacks: "  File \"/Users/hanxiao/Documents/jina/jina/serve/executors/__init__.py\", line 301, in __acall__\n    return await self.__acall_endpoint__(__default_endpoint__, **kwargs)\n"
  stacks: "  File \"/Users/hanxiao/Documents/jina/jina/serve/executors/__init__.py\", line 322, in __acall_endpoint__\n    return func(self, **kwargs)\n"
  stacks: "  File \"/Users/hanxiao/Documents/jina/jina/serve/executors/decorators.py\", line 213, in arg_wrapper\n    return fn(executor_instance, *args, **kwargs)\n"
  stacks: "  File \"/Users/hanxiao/Documents/jina/toy44.py\", line 10, in foo\n    raise NotImplementedError\n"
  stacks: "NotImplementedError\n"
  executor: "MyExec1"
}
```



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

````{admonition} What errors can be handled by the callback?
:class: caution
Callbacks can handle errors that are caused by Executors raising an Exception.

A callback will not receive exceptions:
- from the Gateway having connectivity errors with the Executors.
- between the Client and the Gateway.
````

### Continue streaming when an error occurs

`client.post()` accepts a `continue_on_error` parameter. When set to `True`, the Client will keep trying to send the remaining requests. The `continue_on_error` parameter will only apply
to Exceptions caused by an Executor, but in case of network connectivity issues, an Exception will be raised.

### Transient fault handling with retries

`client.post()` accepts `max_attempts`, `initial_backoff`, `max_backoff` and `backoff_multiplier` parameters to control the capacity to retry requests, when a transient connectivity error occurs, using an exponential backoff strategy.
This can help to overcome transient network connectivity issues. 

The `max_attempts` parameter determines the number of sending attempts, including the original request.
The `initial_backoff`, `max_backoff`, and `backoff_multiplier` parameters determine the randomized delay in seconds before retry attempts.

The initial retry attempt will occur at random(0, initial_backoff). In general, the n-th attempt will occur at random(0, min(initial_backoff*backoff_multiplier**(n-1), max_backoff)).

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
```console  
<DocumentArray (length=1) at 140619524357664>
['Hi there!']
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
```console 
[<jina.types.request.data.DataRequest ('header', 'parameters', 'routes', 'data') at 140619524354592>]
['Hi there!']
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
```console
['Hi there!']
None
```

````

A Client connects to a Flow that processes Documents in an asynchronous and very distributed way. This means that the order of the Flow processing the requests may not be the same order as the Client sending the requests.
However, you can force the order of the results to be deterministic and the same as when they enter the Flow by passing `results_in_order` parameter to {meth}`~jina.clients.mixin.PostMixin.post`.

```python
import random
import time
from jina import Flow, Executor, requests, Client, DocumentArray, Document


class RandomSleepExecutor(Executor):

    @requests
    def foo(self, *args, **kwargs):
        rand_sleep = random.uniform(0.1, 1.3)
        time.sleep(rand_sleep)

f = Flow().add(uses=RandomSleepExecutor, replicas=3)
input_text = [f'ordinal-{i}' for i in range(180)]
input_da = DocumentArray([Document(text=t) for t in input_text])
with f:
    c = Client(port=f.port, protocol=f.protocol)
    output_da = c.post('/', inputs=input_da, request_size=10, results_in_order=True)
    for input, output in zip(input_da, output_da):
        assert input.text == output.text
    
```


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
instrumenting-client
```
