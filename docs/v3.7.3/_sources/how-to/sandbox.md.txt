(sandbox)=
# Sandbox

Sandbox provides a way to run in a cloud environment without any downloading to local. Sandbox will give you a host and port to connect with. Jina automatically takes care of this connection.

Sandbox saves a lot of time when you just want to try out one Executor. It also saves a lot of computing resources for your local machine.

Here is a graph to show the difference between using and not using Sandbox.

```{figure} ../../.github/sandbox-advantage.png
:align: center
```

## Use

```python
from jina import Flow, Document

f = Flow().add(uses='jinahub+sandbox://Hello')

with f:
    r = f.post('/', inputs=Document(text='world'))
    print(r[0].text)
```

This starts a Flow that only has one Executor, and sends a Document to it. The Document is processed by the Executor and the result is returned.

### Use with other Executors


```python
from jina import Flow, Executor, requests, Document


class MyExecutor(Executor):
    @requests
    def process(self, docs, **kwargs):
        for doc in docs:
            doc.text = '(first hello, from MyExecutor)' + doc.text


f = Flow().add(uses=MyExecutor).add(uses='jinahub+sandbox://Hello')

with f:
    r = f.post('/', inputs=Document(text='world'))
    print(r[0].text)
```

## Lifecycle

Sandbox is serverless. It will not be removed immediately after the Flow is closed but kept alive for several minutes. If there is no traffic, it will automatically scale down to 0 to save resources, but it will restart again and give the response whenever a new request is sent to the same Sandbox.

**Sandbox will be shared with other users**. Sometimes you will start the sandbox very quickly because the other users already started it.

It will find the existing sandbox by three factors: 
- Executor name
- Executor tag
- Jina version of the driver program

If all these three factors match, then it will reuse the existing sandboxes.

```{admonition} Caution
:class: caution
If the Jina version of Gateway is later than the latest released Jina version (this happens when you are in the master branch of jina repository), then the sandbox will always be created instead of reused.
```

## Version consistency

The Jina version inside the Sandbox will be the same as the one in the place where the Flow was run. For example, if you run the Flow in your local machine, then it's the version of Jina in your local pip packages.



## Caveats

There are some caveats when using Sandbox Executors with respect to other Executors.

### Un-managed lifetime

Since the lifetime of these Executors is not handled by the Flow and is handled by the Hub infrastructure, there is no way
to override its default configurations, therefore `uses_with`, `uses_metas`, etc ... will not apply.

You can consider a Sandbox Executor as an external Executor where you have no control over its initialization or configuration.

### No GPU support

Computation using GPU is most likely several times faster than using CPU in many use cases. However we don't yet support using a GPU for computation in Sandbox containers.
