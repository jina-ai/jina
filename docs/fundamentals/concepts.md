# Basic Concepts

Document, Executor, and Flow are the three fundamental concepts in Jina. Understanding these will help build your
search.

- [**Document**](Document.md) is the basic data type in Jina;
- [**Executor**](Executor.md) is how Jina processes Documents;
- [**Flow**](Flow.md) is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

## 📄 Document

`Document` is the basic data type that Jina operates with. Text, picture, video, audio, image or 3D mesh: They are
all `Document`s in Jina.

`DocumentArray` is a sequence container of `Document`s. It is the first-class citizen of `Executor`, serving as the
Executor's input and output.

You could say `Document` is to Jina is what `np.float` is to Numpy, and `DocumentArray` is similar to `np.ndarray`.

### Example code

```python
from jina import Document, DocumentArray

doc1 = Document(text="hello world")
doc2 = Document(uri="cute_kittens.png")

docs = DocumentArray([doc1, doc2])
```

````{admonition} See Also
:class: seealso
{ref}`Read more in Document Cookbook <document-cookbook>`
````

## ⚙️ Executor

An `Executor` performs a single task on a `Document` or `DocumentArray`.

### Example code

```python
from jina import Executor, requests


class MyExecutor(Executor):

    @requests
    def foo(self, **kwargs):
        print(kwargs)

```

````{admonition} See Also
:class: seealso
{ref}`Read more in Executor Cookbook <executor-cookbook>`
````

## 🔀 Flow

The `Flow` ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a
dataset

### Example code

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

````{admonition} See Also
:class: seealso
{ref}`Read more in the Flow Cookbook <flow-cookbook>`
````

## 📦 Hub

Jina Hub is a one-stop shop for sharing and reusing Executors. With Hub you can pull prebuilt Executors to dramatically reduce the
effort and complexity needed in your search system, or push your own custom Executors to share privately or publicly.

### Example code

```python
from jina import Flow

f = (Flow()
        .add(uses="jinahub+docker://ImageNormalizer")
        .add(uses="jinahub+docker://BigTransferEncoder")
        .add(uses="jinahub+docker://SimpleIndexer"))
```

````{admonition} See Also
:class: seealso
{ref}`Read more in the Hub Cookbook <hub-cookbook>`
````

## 👹 Daemon

`JinaD` is a daemon for deploying and managing Jina on remote via a RESTful interface. It allows users to
create/update/delete Executors and Flows on remote hosts. It achieves isolation of deployments by defining a `workspace`
for each Jina object, hence allowing a multi-tenant setup with parallel Flows on the same host.

````{admonition} See Also
:class: seealso
{ref}`Read more in the Daemon Cookbook <daemon-cookbook>`
````
