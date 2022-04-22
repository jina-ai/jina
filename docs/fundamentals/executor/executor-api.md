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
:class: hint
Here, `kwargs` are reserved for Jina to inject `metas` and `requests` (representing the request-to-function mapping) values when the Executor is used inside a Flow.

You can access the values of these arguments in the `__init__` body via `self.metas`/`self.requests`/`self.runtime_args`, 
or modify their values before passing them to `super().__init__()`.
````

(exec-endpoint)=
## Methods

Methods of `Executor` can be named and written freely. 

There are, however, special methods inside an `Executor`, which are decorated with `@requests`. When used inside a Flow, these methods are mapped to network endpoints.

(executor-requests)=
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

## Running Executor outside the Flow

`Executor` objects can be used directly, just like any regular Python object.
There are two ways of instantiating an Executor object: From a local Python class, and from the Jina Hub.

````{tab} From local Python
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
````



````{tab} From Jina Hub
You can pull an `Executor` from the Jina Hub and use it directly as a Python object. The [hub](https://hub.jina.ai/) is our marketplace for `Executor`s.

```python
from jina import Executor
from docarray import Document, DocumentArray

executor = Executor.from_hub(uri='jinahub://CLIPTextEncoder', install_requirements=True)

docs = DocumentArray(Document(text='hello'))
executor.encode(docs, {})

print(docs.embeddings.shape)
```
```text
(1, 512)
```
````

(serve-executor-standalone)=
## Serve Executor stand-alone

Executors can be served - and remotely accessed - directly, without the need to instantiate a Flow manually.
This is especially useful when debugging an Executor in a remote setting. It can also be used to run external/shared Executors to be used in multiple Flows.
There are different options how you can deploy and run a stand-alone Executor:
* Run the Executor directly from Python with the `.serve()` class method
* Run the static `Executor.to_k8s_yaml()` method to generate K8s deployment configuration files
* Run the static `Executor.to_docker_compose_yaml()` method to generate a docker-compose service file

### Serving Executors
An Executor can be served using the `.serve()` class method:

````{tab} Serve Executor

```python
from jina import Executor, requests
from docarray import DocumentArray, Document


class MyExec(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0] = 'executed MyExec'  # custom logic goes here


MyExec.serve(port=12345)
```

````

````{tab} Access served Executor

```python
from jina import Client
from docarray import DocumentArray, Document

print(Client(port=12345).post(inputs=DocumentArray.empty(1), on='/foo').texts)
```
```console

```
['executed MyExec']
````

Internally, the `.serve()` method creates a Flow and starts it. Therefore, it can take all associated parameters:
`uses_with`, `uses_metas`, `uses_requests` are passed to the internal `flow.add()` call, `stop_event` is an Event that stops
the Executor, and `**kwargs` is passed to the internal `Flow()` initialisation call.

````{admonition} See Also
:class: seealso

For more details on these arguments and the workings of `Flow`, see the {ref}`Flow section <flow-cookbook>`.
````

### Run Executors in Kubernetes
You can generate Kubernetes configuration files for your containerized Executor by using the static `Executor.to_k8s_yaml()` method. This works very similar to {ref}`deploying a Flow in Kubernetes <kubernetes>`, because your Executor is wrapped automatically in a Flow and using the very same deployment techniques.

```python
from jina import Executor

Executor.to_k8s_yaml(
    output_base_path='/tmp/config_out_folder',
    port_expose=8080,
    uses='jinahub+docker://DummyHubExecutor',
    executor_type=Executor.StandaloneExecutorType.EXTERNAL,
)
```
```shell
kubectl apply -R -f /tmp/config_out_folder
```
The above example will deploy the `DummyHubExecutor` from Jina Hub into your Kubernetes cluster.

````{admonition} Hint
:class: hint
The Executor you are using needs to be already containerized and stored in a registry accessible from your Kubernetes cluster. We recommend Jina Hub for this.
````

(external-shared-executor)=
#### External and shared Executors
The type of stand-alone Executors can be either *external* or *shared*. By default, it will be external.
An external Executor is deployd alongside a {ref}`Gateway <architecture-overview>`. 
A shared Executor has no Gateway. Both types of Executor {ref}`can be used directly in any Flow <external-executor>`.
Having a Gateway may be useful if you want to be able to access your Executor with the {ref}`Client <client>` without an additional Flow. If the Executor will only be used inside other Flows, you should define a shared Executor to save the costs of running the Gateway Pod in Kubernetes.

### Run Executors with Docker Compose
You can generate a Docker Compose service file for your containerized Executor by using the static `Executor.to_docker_compose_yaml()` method. This works very similar to {ref}`running a Flow with Docker Compose <docker-compose>`, because your Executor is wrapped automatically in a Flow and using the very same deployment techniques.

```python
from jina import Executor

Executor.to_docker_compose_yaml(
    output_path='/tmp/docker-compose.yml',
    port_expose=8080,
    uses='jinahub+docker://DummyHubExecutor',
)
```
```shell
 docker-compose -f /tmp/docker-compose.ym up
```
The above example will run the `DummyHubExecutor` from Jina Hub locally on your computer using Docker Compose.

````{admonition} Hint
:class: hint
The Executor you are using needs to be already containerized and stored in an accessible registry. We recommend Jina Hub for this.
````

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
