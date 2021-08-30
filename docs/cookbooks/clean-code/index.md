# Writing Clean & Efficient Code with Jina

Jina is designed as a lean and efficient framework. Solutions built on top of Jina also mean to be so. Here are some
tips to help you write beautiful and efficient code.


1. `from jina import Document, DocumentArray, Executor, Flow, requests` is all you need. Copy-paste it as the first line of your code.

1. Use [Python generator](https://docs.python.org/3/glossary.html#term-generator) as the input to the Flow. Generator can lazily build `Document` one at a time, instead of building all at once. This can greatly speedup the overall performance and reduces the memory footprint.
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


1. Set `request_size`. `request_size` decides how many Documents in each request. When combining with Generator, `request_size` determines how long will it take before sending the first request. You can change `request_size` to overlap the time of request generation and Flow computation.

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


1. No need to implement `__init__` if your `Executor` does not contain initial states.
   
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
   
1. Use `@requests` without specifying `on=` if your function mean to work on all requests. You can use it for catching all requests that are not for this Executor.
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

1. Fold unnecessary arguments into `**kwargs`, only get what you need.
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
   def foo_need_pars_only(self, docs, parameters, docs_matrix, groundtruths_matrix, **kwargs):
      print(parameters)
```
````


1. To debug an `Executor`, there is no need to use it in the Flow. Simply initiate it as an object and call its method.
````{tab} ✅ Do
```python
from jina import Executor, requests, DocumentArray, Document


class MyExec(Executor):

   @requests
   def foo(self, docs, **kwargs):
      for d in docs:
         d.text = 'hello world'


m = MyExec()
da = DocumentArray([Document(text='test')])
m.foo(da)
print(da)
```
````

````{tab} 😔 Don't
```python
from jina import Executor, requests, DocumentArray, Document, Flow


class MyExec(Executor):

   @requests
   def foo(self, docs, **kwargs):
      for d in docs:
         d.text = 'hello world'


da = DocumentArray([Document(text='test')])

with Flow().add(uses=MyExec) as f:
   f.post('/', da, on_done=print)
```
````

   
1. Send `parameters` only request to a Flow if you don't need `docs`.

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
from jina import Executor, Flow, Document, requests

class MyExecutor(Executor):

    @requests
    def foo_need_pars_only(self, parameters, **kwargs):
        print(parameters)

f = Flow().add(uses=MyExecutor)

with f:
    f.post('/foo', inputs=Document(), parameters={'hello': 'world'})
```
````


1. Add `Chunks` to root `Document`, do not create them in one line to keep recursive document structure correct. This is because `chunks` use `ref_doc` to control its `granularity`, at `chunk` creation time, it didn't know anything about its parent, and will get a wrong `granularity` value.

````{tab} ✅ Do
```python
from jina import Document

root_document = Document(text='i am root')
# add one chunk to root
root_document.chunks.append(Document(text='i am chunk 1'))
root_document.chunks.extend([
   Document(text='i am chunk 2'),
   Document(text='i am chunk 3'),
])  # add multiple chunks to root
```
````

````{tab} 😔 Don't
```python
from jina import Document

root_document = Document(
   text='i am root',
   chunks=[
      Document(text='i am chunk 2'),
      Document(text='i am chunk 3'),
   ]
)
```
````
