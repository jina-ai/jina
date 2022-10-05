(architecture-overview)=
# Basic Concepts

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
    Document is the fundamental data structure in Jina for representing multi-modal and cross-modal data. It is the essential element of IO in Jina. More information can be found in [DocArray's Docs](https://docarray.jina.ai/fundamentals/document/). 

**DocumentArray**
    DocumentArray is a list-like container of multiple Documents. More information can be found in [DocArray's Docs](https://docarray.jina.ai/fundamentals/documentarray/). 
    
**Executor**
    {class}`~jina.Executor` is a Python class that has a group of functions using {term}`DocumentArray` as IO. Loosely speaking, each Executor is a microservice. 

**Flow**
    {class}`~jina.Flow` ties multiple {class}`~jina.Executor`s together into a logic pipeline to achieve a task. If an Executor is a microservice, then a Flow is the end-to-end service. 

**Gateway**
    Gateway is the entrypoint of a {term}`Flow`. It exposes multiple protocols for external communications; it routes all internal traffic.
    
**Client**
    {class}`~jina.Client` connects to a {term}`Gateway` and sends/receives data from it.

**Deployment**
    Deployment is an abstraction around {class}`~jina.Executor` that lets the {term}`Gateway` communicate with an Executor. It encapsulates and abstracts internal replication details.

**gRPC, Websocket, HTTP**
    These are network protocols for transmitting data. gRPC is always used for communication between {term}`Gateway` and {term}`Deployment`.

**TLS**
    TLS is a security protocol to facilitate privacy and data security for communications over the Internet. The communication between {term}`Client` and {term}`Gateway` is protected by TLS.
```

## Two coding styles

In the docs, you often see two coding styles when describing a Jina project: 

```{glossary}

**Pythonic**
    The Flow and Executors are all written in Python files, and the entrypoint is via Python.
    
**YAMLish** 
    Executors are written in Python files, and the Flow is defined in a YAML file. The entrypoint is via Jina CLI `jina flow --uses flow.yml`.
```

For example, {ref}`the server-side code<dummy-example>` above follows {term}`Pythonic` style. It can be written in {term}`YAMLish` style as follows:

````{tab} executor.py
```python
from jina import DocumentArray, Executor, requests


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
```
````

````{tab} flow.yml
```yaml
jtype: Flow
with:
  port: 12345
executors:
- uses: FooExec
  replicas: 3
  py_modules: executor.py
- uses: BarExec
  replicas: 2
  py_modules: executor.py
```
````

````{tab} Entrypoint
```bash
jina flow --uses flow.yml
```
````

The YAMLish style separates the Flow representation from the logic code. It is more flexible to configure and should be used for more complex projects in production. In many integrations such as JCloud, Kubernetes, YAMLish is preferred. 

Note that the two coding styles can be converted to each other easily. To load a Flow YAML into Python and run it:

```python
from jina import Flow

f = Flow.load_config('flow.yml')

with f:
    f.block()
```

To dump a Flow into YAML:

```python
from jina import Flow

Flow().add(uses=FooExec, replicas=3).add(uses=BarExec, replicas=2).save_config(
    'flow.yml'
)
```


## Relationship between Jina and DocArray

[DocArray](https://docarray.jina.ai/) is a crucial upstream dependency of Jina. It is the data structure behind Jina. Without DocArray, Jina cannot run.

DocArray contains a set of rich API for on the local and monolith development. Jina scales DocArray to the cloud. The picture below shows their relationship.

```{figure} docarray-jina.svg
```

In a common development journey, your brand-new project first moves horizontally right with DocArray, leveraging all machine learning stacks to improve quality and completing logic in a local environment. At this point, a PoC is built. Then you move vertically up with Jina, enhancing the PoC with a service endpoint, scalability and cloud-native features. Finally, you reach the point where your service is ready for production.


