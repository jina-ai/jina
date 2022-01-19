(sandbox)=

# Jina Sandbox

Jina Sandbox allows you to try out different Jina Executors online and see how they work together without downloading all the Executors to your local machine.

## Prerequisites

- Knowledge about Jina Executor
- Knowledge about Jina Hub

## Start a Flow using Jina Sandbox

```python
from jina import Flow, Document

f = Flow().add(uses='jinahub+sandbox://MiaoTestExecutor1')

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
- Jina version of Gateway

If all these three factors are matched, then it will reuse the existing sandboxes.

```{admonition} Caution
:class: caution
If the Jina version of Gateway is later than the latest released Jina version (things happens when you are in the master branch of jina repository), then the sandbox will always be created instead of reused.
```

## Version Consistency

The Jina version inside the Sandbox will be the same as the one in the place where the Flow was run. For example, if you run the Flow in your local machine, then it's the version of Jina in your local pip packages.

## Mixed with non-sandbox Executors

It can also be mixed with non-sandbox Executors. For example, pure Python class.

```python
from jina import Flow, Document, DocumentArray, Executor, requests

class MyExecutor(Executor):

  @requests
  def process(self, docs: DocumentArray, **kwargs):
    for doc in docs:
      doc.text = '(first hello, from MyExecutor)' + doc.text

      return docs

f = Flow().add(uses=MyExecutor).add(uses='jinahub+sandbox://MiaoTestExecutor1')

with f:
  r = f.post('/', inputs=Document(text='world'), return_results=True)
  print(r[0].text)
```
