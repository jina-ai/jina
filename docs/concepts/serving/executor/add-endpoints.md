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

## Document type binding

When using `docarray>=0.30`, each endpoint bound by the request endpoints can have different input and output Document types. One can specify these types by adding 
type annotations to the decorated methods or by using the `request_schema` and `response_schema` argument. The design is inspired by [FastAPI](https://fastapi.tiangolo.com/). 

These schemas have to be parametrized `DocList` with valid `Documents` inheriting from `BaseDoc`. The only exception is when {ref}`streaming endpoints <streaming-endpoints>` are used, in that case
the `BaseDocs` are the parameters.

When no type annotation or argument is provided, Jina assumes that [LegacyDocument](https://docs.docarray.org/API_reference/documents/documents/#docarray.documents.legacy.LegacyDocument) is the type used.
This is intended to ease the transition from using Jina with `docarray<0.30.0` to using with the newer versions.

```python
from jina import Executor, requests
from docarray import DocList, BaseDoc
from docarray.typing import AnyTensor
from typing import Optional

import asyncio

class BarInputDoc(BaseDoc):
    text: str = ''


class BarOutputDoc(BaseDoc):
    text: str = ''
    embedding: Optional[AnyTensor] = None

class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        print(kwargs)

    @requests(on='/index')
    async def bar(self, docs: DocList[BarInputDoc], **kwargs) -> DocList[BarOutputDoc]:
        print(f'Calling bar')
        await asyncio.sleep(1.0)
        ret = DocList[BarOutputDoc]()
        for doc in docs:
            ret.append(BarOutputDoc(text=doc.text, embedding = embed(doc.text))
        return ret
```

Note that the type hint is actually more that just a hint -- the Executor uses it to infer the actual
schema of the endpoint.

You can also explicitly define the schema of the endpoint by using the `request_schema` and
`response_schema` parameters of the `requests` decorator:

```python
class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        print(kwargs)

    @requests(on='/index', request_schema=DocList[BarInputDoc], response_schema=DocList[BarOutputDoc]) 
    async def bar(self, docs, **kwargs):
        print(f'Calling bar')
        await asyncio.sleep(1.0)
        ret = DocList[BarOutputDoc]()
        for doc in docs:
            ret.append(BarOutputDoc(text=doc.text, embedding = embed(doc.text))
        return ret
```

If there is no `request_schema` and `response_schema`, the type hint is used to infer the schema. If both exist, `request_schema`
and `response_schema` will be used.

(endpoint-arguments)=
## Arguments
All Executor methods decorated by `@requests` need to follow the signature below to be usable as a microservice to be orchestrated either using {class}`~jina.Flow` or {class}`~jina.Deployment`.

The `async` definition is optional.

The endpoint signature looks like the following:

```python
from typing import Dict, Union, Optional, TypeVar
from jina import Executor, requests
from docarray import DocList, BaseDoc

T_input = TypeVar('T_input', bound='BaseDoc')
T_output = TypeVar('T_output', bound='BaseDoc')

class MyExecutor(Executor):
    @requests
    async def foo(
        self,
        docs: DocList[T_input],
        parameters: Dict,
        tracing_context: Optional['Context'],
        **kwargs
    ) -> Union[DocList[T_output], Dict, None]:
        pass
```

Let's take a look at these arguments:

- `docs`: A DocList that is part of the request. Since an Executor wraps functionality related to `DocList`, it's usually the main data format inside Executor methods. Note that these `docs` can be also change in place, just like any other `list`-like object in a Python function.
- `parameters`: A Dict object that passes extra parameters to Executor functions.
- `tracing_context`: Context needed if you want to add {ref}`custom traces <instrumenting-executor>` in your Executor.

````{admonition} Flow-specific arguments
:class: hint
If you use an Executor in a Flow and want to merge incoming DocLists from multiple Executors, you may also be interested in {ref}`some additional arguments <merge-upstream-documentarrays>`.
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

- You can directly return a `DocList` object.
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

(streaming-endpoints)=
## Streaming endpoints
Executors can stream Documents individually rather than as a whole DocList. 
This is useful when you want to return Documents one by one and you want the client to immediately process Documents as 
they arrive. This can be helpful for Generative AI use cases, where a Large Language Model is used to generate text 
token by token and the client displays tokens as they arrive.
Streaming endpoints receive one Document as input and yields one Document at a time.
```{admonition} Note
:class: note

Streaming endpoints are only supported for HTTP protocol and for Deployment.
```

A streaming endpoint has the following signature:

```python
from jina import Executor, requests, Deployment
from docarray import BaseDoc

# first define schemas
class MyDocument(BaseDoc):
    text: str

# then define the Executor
class MyExecutor(Executor):

    @requests(on='/hello')
    async def task(self, doc: MyDocument, **kwargs):
        print()
        # for doc in docs:
        #     doc.text = 'hello world'
        for i in range(100):
            yield MyDocument(text=f'hello world {i}')
            
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
Jina offers a standard python client for using the streaming endpoint:

```python
from jina import Client
client = Client(port=12345, protocol='http', cors=True, asyncio=True)
async for doc in client.stream_doc(
    on='/hello', inputs=MyDocument(text='hello world'), return_type=DocList[MyDocument]
):
    print(doc.text)
```
```text
hello world 0
hello world 1
hello world 2
```

You can also refer to the following Javascript code to connect with the streaming endpoint from your browser:

```html
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
