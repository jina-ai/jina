(exec-endpoint)=
# Add Endpoints

Methods decorated with `@requests` are mapped to network endpoints while serving.

(executor-requests)=
## Decorator

Executor methods decorated with {class}`~jina.requests` are bound to specific network requests, and respond to network queries.

Both `def` or `async def` methods can be decorated with {class}`~jina.requests`.

You can import the `@requests` decorator via:

```python
from jina import requests
```

{class}`~jina.requests` takes an optional `on=` parameter, which binds the decorated method to the specified route:

```python
from jina import Executor, requests
import asyncio


class RequestExecutor(Executor):
    @requests(
        on=['/index', '/search']
    )  # foo is bound to `/index` and `/search` endpoints
    def foo(self, **kwargs):
        print(f'Calling foo')

    @requests(on='/other')  # bar is bound to `/other` endpoint
    async def bar(self, **kwargs):
        await asyncio.sleep(1.0)
        print(f'Calling bar')
```

Run the example:
```python
from jina import Deployment

dep = Deployment(uses=RequestExecutor)
with dep:
    dep.post(on='/index', inputs=[])
    dep.post(on='/other', inputs=[])
    dep.post(on='/search', inputs=[])
```

```shell
─────────────────────── 🎉 Deployment is ready to serve! ───────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC │
│  🏠       Local           0.0.0.0:59525  │
│  🔒     Private      192.168.1.13:59525  │
│  🌍      Public   197.244.143.223:59525  │
╰──────────────────────────────────────────╯
Calling foo
Calling bar
Calling foo
```

### Default binding

A class method decorated with plain `@requests` (without `on=`) is the default handler for all endpoints.
This means it is the fallback handler for endpoints that are not found. `f.post(on='/blah', ...)` invokes `MyExecutor.foo`.

```python
from jina import Executor, requests
import asyncio


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        print(kwargs)

    @requests(on='/index')
    async def bar(self, **kwargs):
        await asyncio.sleep(1.0)
        print(f'Calling bar')
```


### No binding

If a class has no `@requests` decorator, the request simply passes through without any processing.

(endpoint-arguments)=
## Arguments
All Executor methods decorated by `@requests` need to follow the signature below to be usable as a microservice to be orchestrated either using {class}`~jina.Flow` or {class}`~jina.Deployment`.

The `async` definition is optional.

The endpoint signature looks like the following:

```python
from typing import Dict, Union, List, Optional
from jina import Executor, requests, DocumentArray


class MyExecutor(Executor):
    @requests
    async def foo(
        self,
        docs: DocumentArray,
        parameters: Dict,
        tracing_context: Optional['Context'],
        **kwargs
    ) -> Union[DocumentArray, Dict, None]:
        pass

    @requests
    def bar(
        self,
        docs: DocumentArray,
        parameters: Dict,
        tracing_context: Optional['Context'],
        **kwargs
    ) -> Union[DocumentArray, Dict, None]:
        pass
```

Let's take a look at these arguments:

- `docs`: A DocumentArray that is part of the request. Since an Executor wraps functionality related to `DocumentArray`, it's usually the main data format inside Executor methods. Note that these `docs` can be also change in place, just like any other `list`-like object in a Python function.
- `parameters`: A Dict object that passes extra parameters to Executor functions.
- `tracing_context`: Context needed if you want to add {ref}`custom traces <instrumenting-executor>` in your Executor.

````{admonition} Flow-specific arguments
:class: hint
If you use an Executor in a Flow and want to merge incoming DocumentArrays from multiple Executors, you may also be interested in {ref}`some additional arguments <merge-upstream-documentarrays>`.
````

````{admonition} Hint
:class: hint
If you don't need certain arguments, you can suppress them into `**kwargs`. For example:

```{code-block} python
---
emphasize-lines: 7, 11, 16
---
from jina import Executor, requests


class MyExecutor(Executor):

    @requests
    def foo_using_docs_arg(self, docs, **kwargs):
        print(docs)

    @requests
    def foo_using_docs_parameters_arg(self, docs, parameters, **kwargs):
        print(docs)
        print(parameters)

    @requests
    def foo_using_no_arg(self, **kwargs):
        # the args are suppressed into kwargs
        print(kwargs)
```
````

## Returns

Every Executor method can `return` in three ways: 

- You can directly return a `DocumentArray` object.
- If you return `None` or don't have a `return` in your method, then the original `docs` object (potentially mutated by your function) is returned.
- If you return a `dict` object, it will be considered as a result and returned on `parameters['__results__']` to the client.

```python
from jina import requests, Executor, Deployment


class MyExec(Executor):
    @requests(on='/status')
    def status(self, **kwargs):
        return {'internal_parameter': 20}


with Deployment(uses=MyExec) as dep:
    print(dep.post(on='/status', return_responses=True)[0].to_dict()["parameters"])
```

```json
{"__results__": {"my_executor/rep-0": {"internal_parameter": 20.0}}}
```
  

## Streaming endpoints
Executors can stream Documents individually rather than as a whole DocumentArray. 
This is useful when you want to return Documents one by one and you want the client to immediately process Documents as 
they arrive. This can be helpful for Generative AI use cases, where a Large Language Model is used to generate text 
token by token and the client displays tokens as they arrive.
Streaming endpoints receive one Document as input and yields one Document at a time.
A streaming endpoint has the following signature:

```python
from jina import Executor, requests, Document, Deployment

class MyExecutor(Executor):
    @requests(on='/hello')
    async def task(self, doc: Document, **kwargs):
        for i in range(3):
            yield Document(text=f'{doc.text} {i}')
            
with Deployment(
    uses=MyExecutor,
    port=12345,
    protocol='http',
    cors=True,
    include_gateway=False,
) as dep:
    dep.block()
```

From the client side, any SSE client can be used to receive the Documents, one at a time.
Jina offers a standard python client to use the streaming endpoint:

```python
from jina import Client, Document
client = Client(port=12345, protocol='http', cors=True, asyncio=True)
async for doc in client.stream_doc(
    on='/hello', inputs=Document(text='hello world')
):
    print(doc.text )
```
```text
hello world 0
hello world 1
hello world 2
```

You can also refer to the following Javascript code to connect with the streaming endpoint from your browser:

```javascript
<!DOCTYPE html>
<html lang="en">
<body>
<h2>SSE Client</h2>
<script>
    const evtSource = new EventSource("http://localhost:8080/hello?id=1&exec_endpoint=/hello");
    evtSource.addEventListener("update", function(event) {
        // Logic to handle status updates
        console.log(event)
    });
    evtSource.addEventListener("end", function(event) {
        console.log('Handling end....')
        evtSource.close();
    });
</script></body></html>
```
## Exception handling

Exceptions inside `@requests`-decorated functions can simply be raised.

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError('No time for it')
```

````{dropdown} Example usage and output

```python
from jina import Deployment

dep = Deployment(uses=MyExecutor)


def print_why(resp):
    print(resp.status.description)


with dep:
    dep.post('', on_error=print_why)
```

```shell
[...]
executor0/rep-0@28271[E]:NotImplementedError('no time for it')
 add "--quiet-error" to suppress the exception details
[...]
  File "/home/joan/jina/jina/jina/serve/executors/decorators.py", line 115, in arg_wrapper
    return fn(*args, **kwargs)
  File "/home/joan/jina/jina/toy.py", line 8, in foo
    raise NotImplementedError('no time for it')
NotImplementedError: no time for it
NotImplementedError('no time for it')
```

````
