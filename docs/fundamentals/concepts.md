# Basic Concepts

Executor, and Flow are the two fundamental concepts in Jina. Understanding these will help you build your
search engine.

- **Executor** is how Jina processes Documents;
- **Flow** is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

## Executor

An `Executor` performs a single task on a `DocumentArray`.

````{admonition} Example code
:class: tip

```python
from jina import Executor, requests


class MyExecutor(Executor):

    @requests
    def foo(self, **kwargs):
        print(kwargs)

```

````


## Flow

The `Flow` ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying.

````{admonition} Example code
:class: tip

```python
from docarray import Document
from jina import Flow, Executor, requests


class MyExecutor(Executor):

    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


f = Flow().add(name='myexec1', uses=MyExecutor)

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```

````
