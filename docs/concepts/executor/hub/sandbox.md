(sandbox)=
# Sandbox

Sandbox lets you run Executors in a cloud environment without downloading them to your own machine. Sandbox gives you a host and port to connect to. Jina automatically takes care of this connection. This saves a lot of time and compute when you just want to try one Executor.

This graph shows the difference between using and not using Sandbox.

```{figure} ../../../.github/sandbox-advantage.png
:align: center
```

## Using Sandbox

```python
from jina import Flow, Document

f = Flow().add(uses='jinaai+sandbox://jina-ai/Hello')

with f:
    r = f.post('/', inputs=Document(text='world'))
    print(r[0].text)
```

This starts a Flow with one Executor, and sends a Document to it. The Executor processes the Document and returns the result.

### Use with other Executors


```python
from jina import Flow, Executor, requests, Document


class MyExecutor(Executor):
    @requests
    def process(self, docs, **kwargs):
        for doc in docs:
            doc.text = '(first hello, from MyExecutor)' + doc.text


f = Flow().add(uses=MyExecutor).add(uses='jinaai+sandbox://jina-ai/Hello')

with f:
    r = f.post('/', inputs=Document(text='world'))
    print(r[0].text)
```

## Lifecycle

Sandbox is serverless. It will not be removed immediately after the Flow is closed but kept alive for several minutes. If there is no traffic, it will automatically scale down to 0 to save resources, but it will start again and send a response whenever a new request is sent to the same Sandbox.

**Sandboxes are shared with other users**. Sometimes you can access the sandbox quickly because other users have already started it.

Executor Hub finds existing sandboxes based on three factors: 
- Executor name
- Executor tag
- Jina version of the driver program

If all these three factors match, then it will reuse existing sandbox.

```{admonition} Caution
:class: caution
If the Jina version of Gateway is later than the latest released Jina version (which happens when you are in the master branch of jina repository), the sandbox will always be created rather than reused.
```

## Version consistency

The sandboxed Jina version matches your Flow's Jina version. For example, if you run a Jina 3.10 Flow on your local machine, then any sandboxed Executors you run will also use Jina 3.10.

## Caveats

There are some caveats when using Sandbox Executors compared to other Executors:

### Unmanaged lifetime

The lifetime of Sandbox Executors is not handled by the Flow, but rather by the Hub infrastructure, so there is no way
to override its default configurations: You can't use `uses_with`, `uses_metas`.

You can think of a Sandbox Executor as an external Executor where you have no control over its initialization or configuration.

### No GPU support

GPUs are usually several times faster than CPUs. However Sandbox Executors don't yet support GPU computation.
