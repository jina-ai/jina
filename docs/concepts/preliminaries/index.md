(architecture-overview)=
# {fas}`egg` Preliminaries

This chapter introduces the basic terminology you will encounter in the docs. But first, look at the code below:

(dummy-example)=
````{tab} Server
```python
from jina import DocumentArray, Executor, Flow, requests


class FooExec(Executor):
    @requests
    async def add_text(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.text += 'hello, world!'


class BarExec(Executor):
    @requests
    async def add_text(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.text += 'goodbye!'


f = Flow(port=12345).add(uses=FooExec, replicas=3).add(uses=BarExec, replicas=2)

with f:
    f.block()
```
````

````{tab} Client
```python
from jina import Client, DocumentArray

c = Client(port=12345)
r = c.post('/', DocumentArray.empty(2))
print(r.texts)
```
````

Running it gives you:

```text
['hello, world!goodbye!', 'hello, world!goodbye!']
```


This animation shows what's happening behind the scenes:


```{figure} arch-overview.svg
:align: center
```


The following concepts are covered in the user guide:

```{glossary}

**Document**
    Document is the fundamental data structure in Jina for representing multimodal data. It is the essential element of IO in Jina services. More information can be found in [DocArray's Docs](https://docs.docarray.org/fundamentals/document/). 

**DocumentArray**
    DocumentArray is a list-like container of multiple Documents. More information can be found in [DocArray's Docs](https://docarray.jina.ai/fundamentals/documentarray/). 

**Executor**
    {class}`~jina.Executor` is a Python class that can serve logic using {term}`Document`. Loosely speaking, each Executor is a gRPC microservice. 

**Deployment**
    Deployment is a layer that orchestrates {term}`Executor`. It can be used to serve an Executor as a standalone 
    service or as part of a {term}`Flow`. It encapsulates and abstracts internal replication details.

**Flow**
    {class}`~jina.Flow` ties multiple {class}`~jina.Executor`s together into a logic pipeline to achieve a task. If an Executor is a microservice, then a Flow is the end-to-end service. 

**Gateway**
    Gateway is the entrypoint of a {term}`Flow`. It exposes multiple protocols for external communications; it routes all internal traffic.
    
**Client**
    {class}`~jina.Client` connects to a {term}`Gateway` and sends/receives data from it.

**gRPC, WebSocket, HTTP**
    These are network protocols for transmitting data. gRPC is always used for communication between {term}`Gateway` and {term}`Deployment`.

**TLS**
    TLS is a security protocol to facilitate privacy and data security for communications over the Internet. The communication between {term}`Client` and {term}`Gateway` is protected by TLS.
```

```{toctree}
:hidden:

coding-in-python-yaml
```
