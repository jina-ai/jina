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

## Arguments

```python
from typing import Dict, Union, List, Optional
from jina import Executor, requests, DocumentArray


class MyExecutor(Executor):
    @requests
    def foo(
        self,
        docs: DocumentArray,
        parameters: Dict,
        docs_matrix: Optional[List[DocumentArray]],
        docs_map: Optional[Dict[str, DocumentArray]],
    ) -> Union[DocumentArray, Dict, None]:
        pass
```

Let's take a look at these arguments:

- `docs`: A DocumentArray that is part of the request. Since an Executor wraps functionality related to `DocumentArray`, it's usually the main data format inside Executor methods. Note that these `docs` can be also change in place, just like any other `list`-like object in a Python function.
- `parameters`: A Dict object that passes extra parameters to Executor functions.
- `tracing_context`: Context needed if you want to add custom traces. Check {ref}`how to add custom traces in your Executor <instrumenting-executor>`.


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
        print(kwargs['docs_matrix'])
```
````

(async-executors)=
## Async coroutines

You can naturally call async coroutines within {class}`~jina.Executor`s, letting you leverage asynchronous
Python to write concurrent code. 

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    async def encode(self, docs, *kwargs):
        await some_coroutines()
```

This example has a heavy lifting API which we call several times, and we leverage the
async Python features to speed up the {class}`~jina.Executor`'s call by calling the API multiple times concurrently. As a counterpart, in an example without `coroutines`, all 50 API calls are queued and nothing is done concurrently.


````{tab} Async coroutines
```python
import asyncio

from jina import Executor, requests, Document, DocumentArray, Deployment


class DummyAsyncExecutor(Executor):
    @requests
    async def process(self, docs: DocumentArray, **kwargs):
        await asyncio.sleep(1)
        for doc in docs:
            doc.text = doc.text.upper()


with Deployment(uses=DummyAsyncExecutor, port=12345, replicas=2) as dep:
    docs = dep.post(
        on='/index',
        inputs=DocumentArray([Document(text='hello') for _ in range(50)]),
        request_size=1,
        show_progress=True,
    )
```

```shell
────────────────────────── 🎉 Deployment is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:54153  │
│  🔒     Private     192.168.1.187:54153  │
│  🌍      Public    212.231.186.65:54153  │
╰──────────────────────────────────────────╯

  DONE ━━━━━━━━━━━━━━━━━━━━━━ 0:00:01 100% ETA: 0:00:00 50 steps done in 1      
                                                        second  
```

````

````{tab} Sync version
```python
import time

from jina import Executor, requests, DocumentArray, Document, Deployment


class DummyExecutor(Executor):
    @requests
    def process(self, docs: DocumentArray, **kwargs):
        time.sleep(1)
        for doc in docs:
            doc.text = doc.text.upper()


f = Flow().add(uses=DummyExecutor)

with f:
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
        request_size=1,
        show_progress=True,
    )


with Deployment(uses=DummyExecutor, port=12345, replicas=2) as dep:
    docs = dep.post(
        on='/index',
        inputs=DocumentArray([Document(text='hello') for _ in range(50)]),
        request_size=1,
        show_progress=True,
    )
```

```shell
────────────────────────── 🎉 Deployment is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:52340  │
│  🔒     Private     192.168.1.187:52340  │
│  🌍      Public    212.231.186.65:52340  │
╰──────────────────────────────────────────╯

  DONE ━━━━━━━━━━━━━━━━━━━━━━ 0:00:50 100% ETA: 0:00:00 50 steps done in 50     
                                                        seconds        
```
````

Processing data is 50x faster when using `coroutines` because it happens concurrently.

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
    print(dep.post(on='/status').to_dict()["parameters"])
```

```json
{"__results__": {"my_executor/rep-0": {"internal_parameter": 20.0}}}
```
  
## Exception handling

Exceptions inside `@requests`-decorated functions can simply be raised.

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError('no time for it')
```

````{dropdown} Example usage and output

```python
from jina import Deployment

f = Flow().add(uses=MyExecutor)


def print_why(resp, exception):
    print(resp.status.description)


with f:
    f.post('', on_error=print_why)
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
