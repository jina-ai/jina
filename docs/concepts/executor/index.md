(executor-cookbook)=
# {fas}`gears` Executor

An {class}`~jina.Executor` is a self-contained microservice that performs a task on a `DocumentArray`. 

You can create an Executor by extending the `Executor` class and adding logic to endpoint methods.

## Why use Executors?

Once you've learned `DocumentArray`, you can use all its power and expressiveness to build a multimodal application.
But what if you want to go bigger? Organize your code into modules, serve and scale them independently as microservices? That's where Executors come in.

- Executors let you organize DocumentArray-based functions into logical entities that can share configuration state, following OOP.
- Executors can be easily containerized and shared with your colleagues using `jina hub push/pull`.
- Executors can be chained together to form a `~jina.Flow`.

## Minimum working example

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print(docs)  # process docs here
```



```{toctree}
:hidden:

basics
create
add-endpoints
run
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
