(sandbox)=

# Use Hub Executor Remotely

A Jina Executor is often just a Docker image that contains some logic to process Documents. Therefore, you can run it locally if you have Docker installed. But that Docker image could be huge, and you need to download it first then run it afterwards. That would be annoying in many cases.

Jina Sandbox provides a way to download and run in a cloud environment. It will give you a host and port to connect with. Jina automatically takes care of this connection.

It saves a lot of time when you just want to try out one Executor. In addition, it also saves a lot of computing resources for your local machine.

Here is a graph to show the difference between using and not using Sandbox.

```{figure} ../../.github/sandbox-advantage.png
:align: center
```

## Start a Flow using Jina Sandbox

```python
from docarray import Document
from jina import Flow

f = Flow().add(uses='jinahub+sandbox://Hello')

with f:
    r = f.post('/', inputs=Document(text='world'), return_results=True)
    print(r[0].text)
```

This starts a Flow that only has one Executor, and sends a Document to it. The Document is processed by the Executor and the result is returned.

## Sandbox Lifecycle

The sandbox will not be removed immediately after the Flow is closed. It will be kept alive until there is no traffic during this certain period. The default period is currently 15 minutes.

**Sandbox will be shared with other users**. Sometimes you will start the sandbox very quickly because the other users already started it.

It will find the existing sandbox by three factors: 
- Executor name
- Executor tag
- Jina version of the driver program

If all these three factors match, then it will reuse the existing sandboxes.

```{admonition} Caution
:class: caution
If the Jina version of Gateway is later than the latest released Jina version (things happens when you are in the master branch of jina repository), then the sandbox will always be created instead of reused.
```

## Version consistency

The Jina version inside the Sandbox will be the same as the one in the place where the Flow was run. For example, if you run the Flow in your local machine, then it's the version of Jina in your local pip packages.

## Mixed with non-sandbox Executors


```python
from docarray import Document
from jina import Flow, Executor, requests


class MyExecutor(Executor):
    @requests
    def process(self, docs, **kwargs):
        for doc in docs:
            doc.text = '(first hello, from MyExecutor)' + doc.text


f = Flow().add(uses=MyExecutor).add(uses='jinahub+sandbox://Hello')

with f:
    r = f.post('/', inputs=Document(text='world'), return_results=True)
    print(r[0].text)
```

## Caveats

There are some caveats when using Sandbox Executors with respect to other Executors.

### 1. Uncontrolled by Flow

Since the lifetime of these Executors is not handled by the Flow and is handled by the Hub infrastructure, there is no way
to override its default configurations, therefore `uses_with`, `uses_metas`, etc ... will not apply.

You can consider a Sandbox Executor as an external Executor where you have no control over its initialization or configuration.

### 2. No GPU support

Computation using GPU is most likely several times faster than using CPU in many use cases. However we don't yet support using a GPU for computation in Sandbox containers.
