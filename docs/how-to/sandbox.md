(sandbox)=

# How to use Jina Sandbox Executors

It is often the case, that a Jina Executor is just a Docker image that contains some logic to process Documents. Therefore, you can run it locally if you have Docker installed. But the Docker image could be up to several GBs, and you need to download it first, then run it afterwards. That would be annoying in some cases.

Jina Sandbox provides a way to make the downloading and running happen in a cloud environment. It will give back a pair of host and port, which you can connect with. Jina will automatically take care of this connection.

It will save a lot of time when you just want to try out one Executor. In addition, it will also save lot of computing resources for your local machine.

Here is a graph to show the difference between using and not using Sandbox.

```{figure} ../../.github/sandbox-advantage.png
:align: center
```

## Start a Flow using Jina Sandbox

```python
from jina import Flow, Document

f = Flow().add(uses='jinahub+sandbox://Hello')

with f:
  r = f.post('/', inputs=Document(text='world'), return_results=True)
  print(r[0].text)
```

This will start a Flow that only has one online Executor, and will send a document to it. The document will be processed by the Executor and the result will be returned.

## Sandbox Lifecycle

The sandbox will not be removed immediately after the Flow is closed. It will be kept alive until there is no traffic during this certain period. For now, the default period is 15 mins.

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

## Version Consistency

The Jina version inside the Sandbox will be the same as the one in the place where the Flow was run. For example, if you run the Flow in your local machine, then it's the version of Jina in your local pip packages.

## Mixed with non-sandbox Executors


```python
from jina import Flow, Document, DocumentArray, Executor, requests

class MyExecutor(Executor):

  @requests
  def process(self, docs: DocumentArray, **kwargs):
    for doc in docs:
      doc.text = '(first hello, from MyExecutor)' + doc.text

      return docs

f = Flow().add(uses=MyExecutor).add(uses='jinahub+sandbox://Hello')

with f:
  r = f.post('/', inputs=Document(text='world'), return_results=True)
  print(r[0].text)
```

## Caveats

There are some caveats when using Sandbox Executors with respect to other Executors.

### 1. Can't be controlled by the Flow

Since the lifetime of these Executors is not handled by the Flow and is handled by the Hub infrastructure, there is no way
to override its default configurations, therefore `uses_with`, `uses_metas`, etc ... will not apply.

You can consider a Sandbox Executor as an external Executor where you have no control over its initialization or configuration.

### 2. Don't support GPU yet

Computation using GPU is most likely several times faster than using CPU in many use cases. But unfortunately,  we don't support using GPU for computation in Sandbox container yet.
