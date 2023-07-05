(sandbox)=
# Sandbox

Sandbox lets you run Executors in a cloud environment without downloading them to your own machine. Sandbox gives you a host and port to connect to. Jina automatically takes care of this connection. This saves a lot of time and compute when you just want to try one Executor.

This graph shows the difference between using and not using Sandbox.

```{figure} ../../../../../.github/sandbox-advantage.png
:align: center
```

## Using Sandbox

```python
from docarray import Document
from jina import Deployment

dep = Deployment(uses='jinaai+sandbox://jina-ai/Hello')

with dep:
    r = dep.post('/', inputs=Document(text='world'))
    print(r[0].text)
```

This starts a Deployment with one Executor, and sends a Document to it. The Executor processes the Document and returns the result.

## Lifecycle

Sandbox is serverless. It is not removed immediately after the Deployment is closed but kept alive for several minutes. If there is no traffic, it automatically scales down to zero to save resources, but it will start again and send a response whenever a new request is sent to the same Sandbox.

**Sandboxes are shared with other users**. Sometimes you can access the Sandbox quickly because other users have already started it.

Executor Hub finds existing sandboxes based on three factors: 
- Executor name
- Executor tag
- Jina and docarray version of the driver program

If all these three factors match, then Jina reuses the existing sandbox.

```{admonition} Caution
:class: caution
If the Jina version of Gateway is later than the latest released Jina version (which happens when you are in the master branch of jina repository), the Sandbox will always be created rather than reused.
```

## Version consistency

The sandboxed Jina version matches your Deployment's Jina and docarray version. For example, if you run a Jina 3.13 Deployment on your local machine, then any sandboxed Executors you run will also use Jina 3.13.

## Caveats

There are some caveats when using Sandbox Executors compared to other Executors:

### Unmanaged lifetime

The lifetime of Sandbox Executors is not handled by the Deployment, but rather by the Hub infrastructure, so there is no way
to override its default configuration: You can't use `uses_with` or `uses_metas`.

You can think of a Sandbox Executor as an external Executor where you have no control over its initialization or configuration.

### No GPU support

GPUs are usually several times faster than CPUs. However Sandbox Executors don't yet support GPU computation.
