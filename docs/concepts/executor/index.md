(executor-cookbook)=
# Executor

{class}`~jina.Executor` is a self-contained component and performs a group of tasks on a `DocumentArray`. 

You can create an Executor by extending the `Executor` class and adding logic to endpoint methods.


## Why should you use Executors?

Once you have learned `DocumentArray`, you can use all its power and expressiveness to build a multimodal application.
But what if you want to go bigger? Organize your code into modules, serve and scale them independently as microservices? That's exactly what Executors enable you to do.

- Executors let you organize your DocumentArray-based functions into logical entities that can share configuration state, following OOP.

- Executors convert your local functions into functions that can be distributed inside a Flow.

- Executors inside a Flow can process multiple DocumentArrays concurrently, and be deployed easily to the cloud as part of your multimodal application.

- Executors can be easily containerized and shared with your colleagues using `jina hub push/pull`

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
add-endpoints
run
serve
dynamic-batching
health-check
hot-reload
file-structure
containerize
instrumentation
yaml-spec
```