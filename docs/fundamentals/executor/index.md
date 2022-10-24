(executor-cookbook)=
# Executor

{class}`~jina.Executor` is a self-contained component and performs a group of tasks on a `DocumentArray`. 

You can create an Executor by extending the `Executor` class and adding logic to endpoint methods.


## Why should you use Executors?

Once you have learned `DocumentArray`, you can use all its power and expressiveness to build a multi-modal/cross-modal application.
But what if you want to go bigger? Organize your code into modules, serve and scale them independently as microservices? That's exactly what Executors enable you to do.

- Executors let you organize your DocumentArray-based functions into logical entities that can share configuration state, following OOP.

- Executors convert your local functions into functions that can be distributed inside a Flow.

- Executors inside a Flow can process multiple DocumentArrays concurrently, and be deployed easily to the cloud as part of your multi-modal/cross-modal application.

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

executor-api
executor-methods
instrumenting-executor
executor-run
executor-serve
executor-files
containerize-executor
yaml-spec
```