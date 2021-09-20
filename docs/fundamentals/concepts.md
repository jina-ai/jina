# Basic Concepts

Document, Executor, and Flow are the three fundamental concepts in Jina. Understanding these will help build your
search.

- **Document** is the basic data type in Jina;
- **Executor** is how Jina processes Documents;
- **Flow** is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

## Document

`Document` is the basic data type that Jina operates with. Text, picture, video, audio, image or 3D mesh: They are
all `Document`s in Jina.

`DocumentArray` is a sequence container of `Document`s. It is the first-class citizen of `Executor`, serving as the
Executor's input and output.

You could say `Document` is to Jina is what `np.float` is to Numpy, and `DocumentArray` is similar to `np.ndarray`.


````{admonition} Example code
:class: tip

```python
from jina import Document, DocumentArray

doc1 = Document(text="hello world")
doc2 = Document(uri="cute_kittens.png")

docs = DocumentArray([doc1, doc2])
```

````

## Executor

An `Executor` performs a single task on a `Document` or `DocumentArray`.

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

The `Flow` ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a
dataset

````{admonition} Example code
:class: tip

```python
from jina import Flow, Document, Executor, requests


class MyExecutor(Executor):

    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


f = Flow().add(name='myexec1', uses=MyExecutor)

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```

````