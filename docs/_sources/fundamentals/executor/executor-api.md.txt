(executor)=

# Executor API

{class}`~jina.Executor` is a self-contained component and performs a group of tasks on a `DocumentArray`. 
It encapsulates functions that process `DocumentArray`s. Inside the Executor, these functions are decorated with `@requests`. To create an Executor, you only need to follow three principles:

1. An `Executor` should subclass directly from the `jina.Executor` class.
2. An `Executor` class is a bag of functions with shared state or configuration (via `self`); it can contain an arbitrary number of
  functions with arbitrary names.
3. Functions decorated by `@requests` will be invoked according to their `on=` endpoint. These functions can be coroutines (`async def`) or regular functions.

## Constructor

### Subclass

Every new executor should be a subclass of {class}`~jina.Executor`.

You can name your executor class freely.

### `__init__`

No need to implement `__init__` if your `Executor` does not contain initial states.

If your executor has `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)`
in the body:

```python
from jina import Executor


class MyExecutor(Executor):
    def __init__(self, foo: str, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
        self.foo = foo
```


````{admonition} What is inside kwargs? 
:class: tip
Here, `kwargs` are reserved for Jina to inject `metas` and `requests` (representing the request-to-function mapping) values when the Executor is used inside a Flow.

You can access the values of these arguments in the `__init__` body via `self.metas`/`self.requests`/`self.runtime_args`, 
or modify their values before passing them to `super().__init__()`.
````

## Methods

Methods of `Executor` can be named and written freely. 

There are, however, special methods inside an `Executor`, which are decorated with `@requests`. When used inside a Flow, these methods are mapped to network endpoints.

### Method decorator

Executor methods decorated with `@requests` are bound to specific network requests, and respond to network queries.

Both `def` or `async def` function can be decorated with `@requests`.

You can import the `requests` decorator via

```python
from jina import requests
```

`requests` is a decorator that takes an optional parameter: `on=`. It binds the decorated method of the `Executor` to the specified route. 

```python
from jina import Executor, requests
import asyncio


class RequestExecutor(Executor):
    @requests(
        on=['/index', '/search']
    )  # foo will be bound to `/index` and `/search` endpoints
    def foo(self, **kwargs):
        print(f'Calling foo')

    @requests(on='/other')  # bar will be bound to `/other` endpoint
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

```console
           Flow@18048[I]:🎉 Flow is ready to use!                                                   
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:52255
	🔒 Private network:	192.168.1.187:52255
	🌐 Public address:	212.231.186.65:52255
Calling foo
Calling bar
Calling foo
```

#### Default binding

A class method decorated with plain `@requests` (without `on=`) is the default handler for all endpoints.
That means it is the fallback handler for endpoints that are not found. `f.post(on='/blah', ...)` will invoke `MyExecutor.foo`.

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


#### No binding

A class with no `@requests` binding plays no part in the Flow. 
The request will simply pass through without any processing.

### Method arguments

All Executor methods decorated by `@requests` need to follow the signature below in order to be usable as a microservice inside a `Flow`.
The `async` definition is optional.


```python
from typing import Dict, Union, List
from docarray import DocumentArray
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    async def foo(
        self, docs: DocumentArray, parameters: Dict, docs_matrix: List[DocumentArray]
    ) -> Union[DocumentArray, Dict, None]:
        pass
```

Let's take a look at all these arguments:

- `docs`: A `DocumentArray` that is part of the request. Since the nature of `Executor` is to wrap functionality related to `DocumentArray`, it is usually the main processing unit inside `Executor` methods. It is important to notice that these `docs` can be also changed in place, just like it could happen with 
any other `list`-like object in a Python function.

- `parameters`: A Dict object that can be used to pass extra parameters to the `Executor` functions.

- `docs_matrix`:  This is the least common parameter to be used for an `Executor`. This argument is needed when an `Executor` is used inside a `Flow` to merge or reduce the output of more than one other `Executor`.
As a user, you will rarely touch this parameter. 



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

### Method return

Every Executor method can `return` in 3 ways: 

- If you return a `DocumentArray` object, then it will be sent over to the next Executor.
- If you return `None` or if you don't have a `return` in your method, then the original `doc` object (potentially mutated by your function) will be sent over to the next Executor.
- If you return a `dict` object, then it will be considered as a result and passed on behind `parameters['__results__']`. The original `doc` object (potentially mutated by your function) will be sent over to the next Executor.
  

### Example

Let's understand how `Executor`s process `DocumentArray`s inside a Flow, and how the changes are chained and applied, affecting downstream `Executors` in the Flow.

<details>
<summary>Code and output</summary>

```python
from docarray import DocumentArray, Document
from jina import Executor, requests, Flow


class PrintDocuments(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(f' PrintExecutor: received document with text: "{doc.text}"')


class ProcessDocuments(Executor):
    @requests(on='/change_in_place')
    def in_place(self, docs, **kwargs):
        # This executor will only work on `docs` and will not consider any other arguments
        for doc in docs:
            print(f' ProcessDocuments: received document with text "{doc.text}"')
            doc.text = 'I changed the executor in place'

    @requests(on='/return_different_docarray')
    def ret_docs(self, docs, **kwargs):
        # This executor will only work on `docs` and will not consider any other arguments
        ret = DocumentArray()
        for doc in docs:
            print(f' ProcessDocuments: received document with text: "{doc.text}"')
            ret.append(Document(text='I returned a different Document'))
        return ret


f = Flow().add(uses=ProcessDocuments).add(uses=PrintDocuments)

with f:
    f.post(on='/change_in_place', inputs=DocumentArray(Document(text='request')))
    f.post(
        on='/return_different_docarray', inputs=DocumentArray(Document(text='request'))
    )
```


```console
           Flow@23300[I]:🎉 Flow is ready to use!                                                   
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:61855
	🔒 Private network:	192.168.1.187:61855
	🌐 Public address:	212.231.186.65:61855
 ProcessDocuments: received document with text "request1"
 PrintExecutor: received document with text: "I changed the executor in place"
 ProcessDocuments: received document with text: "request2"
 PrintExecutor: received document with text: "I returned a different Document"
```

</details>

## Other usages

Beside running Executor inside the Flow, we list two other usages that may help you debug.  

### Use Executor out of Flow

`Executor` objects can be used directly, just like a regular Python object. For example:

```python
from docarray import DocumentArray, Document
from jina import Executor, requests


class MyExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            d.text = 'hello world'


m = MyExec()
da = DocumentArray([Document(text='test')])
m.foo(da)
print(f'Text: {da[0].text}')
```

```text
Text: hello world
```


### Use async Executors


```python
import asyncio
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    async def foo(self, **kwargs):
        await asyncio.sleep(1.0)
        print(kwargs)


async def main():
    m = MyExecutor()
    call1 = asyncio.create_task(m.foo())
    call2 = asyncio.create_task(m.foo())
    await asyncio.gather(call1, call2)


asyncio.run(main())
```

## See further

- {ref}`Executor in Flow <executor-in-flow>` 
- {ref}`Debugging an Executor <debug-executor>`
- {ref}`Using an Executor on a GPU <gpu-executor>`
- {ref}`How to use external Executors <external-executor>`
