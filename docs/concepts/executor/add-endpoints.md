(exec-endpoint)=
# Add Endpoints

Methods decorated with `@requests` are mapped to network endpoints while serving.

(executor-requests)=
## Decorator

Executor methods decorated with {class}`~jina.requests` are bound to specific network requests, and respond to network queries.

Both `def` or `async def` functions can be decorated with {class}`~jina.requests`.

You can import the `@requests` decorator via

```python
from jina import requests
```

{class}`~jina.requests` is a decorator that takes an optional `on=` parameter. It binds the decorated method of the Executor to the specified route. 

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

```python
from jina import Flow

f = Flow().add(uses=RequestExecutor)

with f:
    f.post(on='/index', inputs=[])
    f.post(on='/other', inputs=[])
    f.post(on='/search', inputs=[])
```

```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:55925  │
│  🔒     Private     192.168.1.187:55925  │
│  🌍      Public    212.231.186.65:55925  │
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

A class with no `@requests` binding plays no part in the Flow. 
The request simply passes through without any processing.

## Arguments

All Executor methods decorated by `@requests` need to follow the signature below to be usable as a microservice inside a {class}`~jina.Flow`.
The `async` definition is optional.

```python
from typing import Dict, Union, List, Optional
from jina import Executor, requests, DocumentArray


class MyExecutor(Executor):
    @requests
    async def foo(
        self,
        docs: DocumentArray,
        parameters: Dict,
        docs_matrix: Optional[List[DocumentArray]],
        docs_map: Optional[Dict[str, DocumentArray]],
    ) -> Union[DocumentArray, Dict, None]:
        pass

    @requests
    def bar(
        self,
        docs: DocumentArray,
        parameters: Dict,
        docs_matrix: Optional[List[DocumentArray]],
        docs_map: Optional[Dict[str, DocumentArray]],
    ) -> Union[DocumentArray, Dict, None]:
        pass
```

Let's take a look at these arguments:

- `docs`: A DocumentArray that is part of the request. Since the nature of Executor is to wrap functionality related to `DocumentArray`, it's usually the main processing unit inside Executor methods. It's important to notice that these `docs` can be also changed in place, just like
any other `list`-like object in a Python function.

- `parameters`: A Dict object that passes extra parameters to Executor functions.

- `docs_matrix`:  This is one of the least common parameters to be used for an Executor. It is passed when multiple parallel branches lead into the Executor, and `no_reduce=True` is set. Each DocumentArray in the matrix is the output of one previous Executor.
 
- `docs_map`:  This is also one of the least common parameter to be used for an Executor. It has the same utility as `docs_matrix` but the information comes as a dict with previous Executor names as keys, and DocumentArrays as values.

- `tracing_context`: Context needed if you want to add custom traces. Check {ref}`how to add custom traces in your Executor <instrumenting-executor>`.


````{admonition} Hint
:class: hint
If you don't need some arguments, you can suppress them into `**kwargs`. For example:

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


### Multiple DocumentArrays as input argument

You have seen that {class}`~jina.Executor` methods can receive multiple parameters.

`docs_matrix` and `docs_map` are only used in some special cases.

One case is when an Executor receives messages from more than one incoming {class}`~jina.Executor` in the {class}`~jina.Flow`:

If you set `no_reduce` to True and the Executor has more than one incoming Executor, the Executor will receive all the DocumentArrays coming from previous Executors independently under `docs_matrix` and `docs_map`.
If `no_reduce` is not set or set to False, `docs_map` and `docs_matrix` will be None and the Executor will receive a single DocumentArray resulting from the reducing of all the incoming ones.

```python
from jina import Flow, Executor, requests, Document, DocumentArray


class Exec1(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec1'


class Exec2(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec2'


class MergeExec(Executor):
    @requests
    def foo(self, docs_matrix, **kwargs):
        documents_to_return = DocumentArray()
        for doc1, doc2 in zip(*docs_matrix):
            print(
                f'MergeExec processing pairs of Documents "{doc1.text}" and "{doc2.text}"'
            )
            documents_to_return.append(
                Document(text=f'Document merging from "{doc1.text}" and "{doc2.text}"')
            )
        return documents_to_return


f = (
    Flow()
    .add(uses=Exec1, name='exec1')
    .add(uses=Exec2, name='exec2')
    .add(uses=MergeExec, needs=['exec1', 'exec2'], no_reduce=True)
)

with f:
    returned_docs = f.post(on='/', inputs=Document())

print(f'Resulting documents {returned_docs[0].text}')
```


```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:55761  │
│  🔒     Private     192.168.1.187:55761  │
│  🌍      Public    212.231.186.65:55761  │
╰──────────────────────────────────────────╯

MergeExec processing pairs of Documents "Exec1" and "Exec2"
Resulting documents Document merging from "Exec1" and "Exec2"
```

When merging Documents from more than one upstream {class}`~jina.Executor`, sometimes you want to control which Documents come from which Executor.
Executor will receive the `docs_map` as a dictionary where the key will be the last Executor processing that previous request and the DocumentArray of the request as the values.

```python
from jina import Flow, Executor, requests, Document


class Exec1(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec1'


class Exec2(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec2'


class MergeExec(Executor):
    @requests
    def foo(self, docs_map, **kwargs):
        print(docs_map)


f = (
    Flow()
    .add(uses=Exec1, name='exec1')
    .add(uses=Exec2, name='exec2')
    .add(uses=MergeExec, needs=['exec1', 'exec2'], no_reduce=True)
)

with f:
    f.post(on='/', Document())
```


```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:56286  │
│  🔒     Private     192.168.1.187:56286  │
│  🌍      Public    212.231.186.65:56286  │
╰──────────────────────────────────────────╯

{'exec1': <DocumentArray (length=1) at 140270975034640>, 'exec2': <DocumentArray (length=1) at 140270975034448>}
```

(async-executors)=
## Async coroutines


You can naturally call async coroutines within {class}`~jina.Executor`'s, allowing you to leverage the power of asynchronous
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

from jina import Flow, Executor, requests, Document, DocumentArray


class DummyAsyncExecutor(Executor):
    @requests
    async def process(self, docs: DocumentArray, **kwargs):
        await asyncio.sleep(1)
        for doc in docs:
            doc.text = doc.text.upper()


f = Flow().add(uses=DummyAsyncExecutor)

with f:
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
        request_size=1,
        show_progress=True,
    )
```

```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
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

from jina import Flow, Executor, requests, DocumentArray, Document


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
```

```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
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

Processing the data is 50x faster when using `coroutines` because it happens concurrently.


### Call another Jina Flow 
To call other another Jina Flow using `Client` from an `Executor`, you also need to use `async def` and async Client.


```python
from jina import Client, Executor, requests, DocumentArray


class DummyExecutor(Executor):

    c = Client(host='grpc://0.0.0.0:51234', asyncio=True)

    @requests
    async def process(self, docs: DocumentArray, **kwargs):
        self.c.post('/', docs)
```


## Returns

Every Executor method can `return` in three ways: 

- If you return a `DocumentArray` object, then it will be sent to the next Executor.
- If you return `None` or don't have a `return` in your method, then the original `docs` object (potentially mutated by your function) will be sent to the next Executor.
- If you return a `dict` object, it will be considered as a result and returned on `parameters['__results__']` to the client. `__results__` key will not be available in subsequent Executors. The original `docs` object (potentially mutated by your function) will be sent to the next Executor.


```python
from jina import requests, Executor, Flow


class MyExec(Executor):
    @requests(on='/status')
    def status(self, **kwargs):
        return {'internal_parameter': 20}


f = Flow().add(uses=MyExec, name='my_executor')

with f:
    print(f.post(on='/status').to_dict()["parameters"])
```

```json
{"__results__": {"my_executor/rep-0": {"internal_parameter": 20.0}}}
```
  
## Exception handling

Exceptions raised inside `@requests`-decorated functions can simply be raised. The Flow handles it.

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError('no time for it')
```

````{dropdown} Example usage and output

```python
from jina import Flow

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

## Example

Let's understand how Executor's process DocumentArray's inside a Flow, and how changes are chained and applied, affecting downstream Executors in the Flow.


```python 
from jina import Executor, requests, Flow, DocumentArray, Document


class PrintDocuments(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(f' PrintExecutor: received document with text: "{doc.text}"')


class ProcessDocuments(Executor):
    @requests(on='/change_in_place')
    def in_place(self, docs, **kwargs):
        # This Executor only works on `docs` and doesn't consider any other arguments
        for doc in docs:
            print(f' ProcessDocuments: received document with text "{doc.text}"')
            doc.text = 'I changed the executor in place'

    @requests(on='/return_different_docarray')
    def ret_docs(self, docs, **kwargs):
        # This executor only works on `docs` and doesn't consider any other arguments
        ret = DocumentArray()
        for doc in docs:
            print(f' ProcessDocuments: received document with text: "{doc.text}"')
            ret.append(Document(text='I returned a different Document'))
        return ret


f = Flow().add(uses=ProcessDocuments).add(uses=PrintDocuments)

with f:
    f.post(on='/change_in_place', inputs=DocumentArray(Document(text='request1')))
    f.post(
        on='/return_different_docarray', inputs=DocumentArray(Document(text='request2'))
    )
```


```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:58746  │
│  🔒     Private     192.168.1.187:58746  │
│  🌍      Public    212.231.186.65:58746  │
╰──────────────────────────────────────────╯

 ProcessDocuments: received document with text "request1"
 PrintExecutor: received document with text: "I changed the executor in place"
 ProcessDocuments: received document with text: "request2"
 PrintExecutor: received document with text: "I returned a different Document"
```
