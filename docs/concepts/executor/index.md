(executor-cookbook)=
# {fas}`gears` Executor

An {class}`~jina.Executor` is a self-contained microservice that performs a task on a `DocumentArray`. 

You can create an Executor by extending the `Executor` class and adding logic to endpoint methods.

There is a wide selection of pre-built Executors available on Jina AI's [Executor Hub](https://cloud.jina.ai/executors). See the {ref}`Hub section <jina-hub>` for more information.

## Why use Executors?

Once you've learned `DocumentArray`, you can use all its power and expressiveness to build a multimodal application.
But what if you want to go bigger? Organize your code into modules, serve and scale them independently as microservices? That's where Executors come in.

- Executors let you organize DocumentArray-based functions into logical entities that can share configuration state, following OOP.
- Executors can be easily containerized and shared with your colleagues using `jina hub push/pull`.
- Executors can be chained together to form a `~jina.Flow`.

## Minimum working example

```python
from jina import Executor, requests, DocumentArray, Document


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            d.text = 'hello world'


executor = MyExecutor()
docs = DocumentArray([Document(text='hello')])

executor.foo(da)
print(f'Text: {docs[0].text}')
```

```text
Text: hello world
```

```{toctree}
:hidden:

basics
create
add-endpoints
serve
dynamic-batching
health-check
hot-reload
file-structure
containerize
instrumentation
executor-in-flow
docarray-v2
yaml-spec
```
