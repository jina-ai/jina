(architecture-overview)=
# Basic Concepts

This chapter introduces the basic terminologies you will encounter in the docs. But first, let's look at the code below:

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


What happens underneath is depicted in the following animation:


```{figure} arch-overview.svg
:align: center
```


The following concepts will be covered in the user guide:

```{glossary}

**Document**
    Document is the fundamental data structure in Jina for representing multi-modal and cross-modal data. It is the essential element of IO in Jina. More information can be found in [DocArray's Docs](https://docarray.jina.ai/fundamentals/document/). 

**DocumentArray**
    DocumentArray is a list-like container of multiple Documents. More information can be found in [DocArray's Docs](https://docarray.jina.ai/fundamentals/documentarray/). 
    
**Executor** 
    {class}`~jina.Executor` is a Python class that has a group of functions using {term}`DocumentArray` as IO. Loosely speaking, each Executor is a microservice. 

**Flow**
    {class}`~jina.Flow` ties multiple {class}`~jina.Executor`s together into a logic pipeline to achieve a task. If Executor is a microservice, then Flow is the end-to-end service. 

**Gateway**
    Gateway is the entrypoint of a {term}`Flow`. It exposes multiple protocols for external communications; it routes all internal traffics.
    
**Client**
    {class}`~jina.Client` is for connecting to a {term}`Gateway` and sending/receiving data from it.

**Deployment**
    Deployment is an abstraction around {class}`~jina.Executor` that lets the {term}`Gateway` communicate with an Executor. It encapsulates and abstracts internal replication details.

**gRPC, Websocket, HTTP**
    They are network protocols for transmitting data. gRPC is always used between {term}`Gateway` and {term}`Deployment` communication.

**TLS**
    TLS is a security protocol designed to facilitate privacy and data security for communications over the Internet. The communication between {term}`Client` and {term}`Gateway` is protected by TLS.
```

## Relationship between Jina and DocArray

[DocArray](https://docarray.jina.ai/) is a crucial upstream dependency of Jina. It is the data structure behind Jina. Without DocArray, Jina can not run.

DocArray contains a set of rich API for on the local & monolith development. Jina scales DocArray to the cloud. The picture below shows their relationship.

```{figure} docarray-jina.svg
```

In a common development journey, a brand-new project first moves horizontally left with DocArray, leveraging all machine learning stacks to improve quality and completing logics in a local environment. At this point, a POC is built. Then move vertically up with Jina, enhancing the POC with service endpoint, scalability and cloud-native features. Finally, you reach to the point where your service is ready for production.


