(architecture-overview)=
# {fas}`egg` Preliminaries

This chapter introduces the basic terminology and concepts you will encounter in the docs. But first, look at the code below:

(dummy-example)=
````{tab} Server
```python
from jina import Executor, Flow, requests
from docarray import DocList
from docarray.documents import TextDoc


class FooExec(Executor):
    @requests
    async def add_text(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for d in docs:
            d.text += 'hello, world!'


class BarExec(Executor):
    @requests
    async def add_text(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for d in docs:
            d.text += 'goodbye!'

f = Flow(port=12345).add(uses=FooExec, replicas=3).add(uses=BarExec, replicas=2)

with f:
    f.block()
```
````

````{tab} Client
```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

r = c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])
print([d.text for d in r])
```
````

Running it gives you:

```text
['hello, world!goodbye!', 'hello, world!goodbye!']
```

## Architecture
This animation shows what's happening behind the scenes when running the previous example:


```{figure} arch-overview.svg
:align: center
```

```{hint}
:class: seealso
GRPC, WebSocket, HTTP are network protocols for transmitting data. gRPC is always used for communication between {term}`Gateway` and {term}`Executor`.
```

```{hint}
:class: seealso
TLS is a security protocol to facilitate privacy and data security for communications over the Internet. The communication between {term}`Client` and {term}`Gateway` is protected by TLS.
```

Jina as an MLOPs framework is structured in two main layers that together with DocArray data structure and Jina Python Client complete the framework, all of them are covered in the user guide
and contains the following concepts:

```{glossary}

**DocArray data structure**

Data structures coming from [docarray](https://docs.docarray.org/) are the basic fundamental data structure in Jina.


- **BaseDoc**
    Document is the basic object for representing multimodal data. It can be extended to represent any data you want. More information can be found in [DocArray's Docs](https://docs.docarray.org/user_guide/representing/first_step/). 

- **DocList**
    DocList is a list-like container of multiple Documents. It is the essential element of IO in Jina services. More information can be found in [DocArray's Docs](https://docs.docarray.org/user_guide/representing/array/). 

**Serving**

This layer contains all the objects and concepts that are used to actually serve the logic and receive and respond to queries. These components are designed to be used as microservices ready to be containerized. 
These components can be orchestrated by Jina's {term}`orchestration` layer or by other container orchestration frameworks such as Kubernetes or Docker Compose.
 

- **Executor**
    {class}`~jina.Executor` is a Python class that can serve logic using {term}`DocList`. Loosely speaking, each Executor is a microservice.

- **Gateway**
    Gateway is the entrypoint of a {term}`Flow`. It exposes multiple protocols for external communications; it routes all internal traffic.


**Orchestration**

This layer contains the components making sure that the objects (especially the {term}`Executor`) are deployed and scaled for serving.
They wrap them to provide them the **scalability** and **serving** capabilities. They also provide easy translation to other orchestration
frameworks (Kubernetes, Docker compose) to provide more advanced and production-ready settings. They can also be directly deployed to [Jina AI Cloud](https://cloud.jina.ai)
with a single command line.


- **Deployment**
    Deployment is a layer that orchestrates {term}`Executor`. It can be used to serve an Executor as a standalone 
    service or as part of a {term}`Flow`. It encapsulates and abstracts internal replication and serving details.

- **Flow**
    {class}`~jina.Flow` ties multiple {class}`~jina.Deployments`s together into a logic pipeline to achieve a more complex task. It orchestrates both {term}`Executor`s and the {term}`Gateway`.

**Client**
{class}`~jina.Client` connects to a {term}`Gateway` or {term}`Executor` and sends/receives/streams data from it.

```

```{admonition} Deployments on JCloud
:class: important
At present, JCloud is only available for Flows. We are currently working on supporting Deployments.
```

```{toctree}
:hidden:

coding-in-python-yaml
```
