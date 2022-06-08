# How to write clean & efficient code

Jina is designed as a lean and efficient framework. Solutions built on top of Jina also mean to be so. Here are some
tips to help you write beautiful and efficient code.

## Clean import

```python
from jina import Executor, Flow, requests, Document, DocumentArray
```
is often all you need. Copy-paste it as the first line of your code.

## Generator as Flow input

Use a [Python generator](https://docs.python.org/3/glossary.html#term-generator) as the input to the Flow. A generator can lazily build `Document`s one at a time, instead of building them all at once. This can greatly speed up overall performance and reduce the memory footprint.
````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 3, 4, 5
---

from jina import Flow, Document

def my_input():
   for _ in range(1000):
      yield Document()

f = Flow()
with f:
   f.post('/', my_input)
```
````

````{tab} 😔 Don't
```python
from jina import Flow, Document, DocumentArray

my_input = DocumentArray([Document() for _ in range(1000)])

f = Flow()
with f:
    f.post('/', my_input)
```
````

## Set `request_size`

`request_size` defines how many Documents to send in each request. When combined with a Generator, `request_size` determines how long it will take before sending the first request. You can change `request_size` to overlap the time of request generation and Flow computation.

````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 10
---

from jina import Flow, Document

def my_input():
   for _ in range(1000):
      # big document
      yield Document()

f = Flow().add(uses=...)  # heavy computation
with f:
   f.post('/', my_input, request_size=10)
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 10
---

from jina import Flow, Document

def my_input():
   for _ in range(1000):
      # big document
      yield Document()

f = Flow().add(uses=...)  # heavy computation
with f:
   f.post('/', my_input, request_size=10000)
```
````

## Skip unnecessary `__init__` 

No need to implement `__init__` if your `Executor` does not contain initial states.
   
````{tab} ✅ Do
```python
from jina import Executor


class MyExecutor(Executor):
    def foo(self, **kwargs):
        ...
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 4, 5
---
from jina import Executor

class MyExecutor(Executor):
   def __init__(**kwargs):
      super().__init__(**kwargs)

   def foo(self, **kwargs):
      ...
```
````

## Skip unnecessary `@requests(on=...)`
   
Use `@requests` without specifying `on=` if your function is meant to work on all requests. You can use it for catching all requests that are not for this Executor.
````{tab} ✅ Do
```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def _skip_all(self, **kwargs):
        print('default do sth')
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 4, 8
---
from jina import Executor

class MyExecutor(Executor):
   @requests(on='/index')
   def _skip_index(self, **kwargs):
      pass
   
   @requests(on='/search')
   def _skip_search(self, **kwargs):
      pass
```
````

## Skip unnecessary `**kwargs`

Fold unnecessary arguments into `**kwargs`, only get what you need.
````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 6
---
from jina import Executor, requests

class MyExecutor(Executor):

   @requests
   def foo_need_pars_only(self, parameters, **kwargs):
      print(parameters)
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 6
---
from jina import Executor, requests

class MyExecutor(Executor):

   @requests
   def foo_need_pars_only(self, docs, parameters, docs_matrix, **kwargs):
      print(parameters)
```
````


## Send `parameters`-only request
   
Send a `parameters`-only request to a Flow if you don't need `docs`.

````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 12
---
from jina import Executor, Flow, requests

class MyExecutor(Executor):

    @requests
    def foo_need_pars_only(self, parameters, **kwargs):
        print(parameters)

f = Flow().add(uses=MyExecutor)

with f:
    f.post('/foo', parameters={'hello': 'world'})
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 12
---
from docarray import Document
from jina import Executor, Flow, requests

class MyExecutor(Executor):

    @requests
    def foo_need_pars_only(self, parameters, **kwargs):
        print(parameters)

f = Flow().add(uses=MyExecutor)

with f:
    f.post('/foo', inputs=Document(), parameters={'hello': 'world'})
```
````

## Heavy lifting in the Flow, not in the Client
   
Heavy-lifting jobs should be put into an `Executor` if possible.
For instance, sending high-resolution images to the Flow
can be time-consuming. Putting it into an Executor can leverage the Flow to scale it.
It also reduces the network overhead.

````{tab} ✅ Do
```python
import glob

from docarray import Document
from jina import Executor, Flow, requests


class MyExecutor(Executor):
    @requests
    def to_blob_conversion(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.load_uri_to_image_tensor()  # conversion happens inside Flow


f = Flow().add(uses=MyExecutor, replicas=2)


def my_input():
    image_uris = glob.glob('/.workspace/*.png')
    for image_uri in image_uris:
        yield Document(uri=image_uri)


with f:
    f.post('/foo', inputs=my_input)
```
````

````{tab} 😔 Don't
```python
import glob

from docarray import Document
from jina import Executor


def my_input():
    image_uris = glob.glob('/.workspace/*.png')  # load high resolution images.
    for image_uri in image_uris:
        doc = Document(uri=image_uri)
        doc.load_uri_to_image_tensor()  # time consuming-job on client side
        yield doc


f = Flow().add()

with f:
    f.post('/foo', inputs=my_input)
```
````


## Keep only necessary fields

Sometimes you do not want to pass the full Document to subsequent Executors for reasons of efficiency. 
You can simply use the `.pop` method to remove those fields.

When using Jina with an HTTP frontend, the frontend often does not need `ndarray` or binary content. Hence, 
fields such as `blob`, `embedding`, and `buffer` can often be removed at the last Executor before returning the final results to the frontend.

````{tab} ✅ Do

```{code-block} python
---
emphasize-lines: 9
---
from jina import Executor, requests

class FirstExecutor(Executor):
    
    @requests
    def foo(self, docs, **kwargs):
        # some process on docs
        for d in docs:
            d.pop('embedding', 'blob')

class SecondExecutor(Executor):
    
    @requests
    def bar(self, docs, **kwargs):
        # do follow up processing, but now `.embedding` and `.blob` is empty
        # but that's fine because this Executor does not need those fields 
```

````

````{tab} 😔 Don't

```python

from jina import Executor, requests

class FirstExecutor(Executor):

    @requests
    def foo(self, docs, **kwargs):
        # some process on docs

class SecondExecutor(Executor):

    @requests
    def bar(self, docs, **kwargs):
        # do follow up processing, even though `.embedding` and `.blob` are never used 
```

````
