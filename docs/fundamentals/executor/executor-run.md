# Run

You can use {class}`~jina.Executor` objects directly, just like a regular Python object.

There are two ways to instantiate an Executor object: From a local Python class, or from Jina Hub:

````{tab} From local Python
You can use `Executor` objects directly, just like a regular Python object:

```python
from jina import Executor, requests, DocumentArray, Document


class MyExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            d.text = 'hello world'


m = MyExec()
da = DocumentArray([Document(text='test')])
m.foo(da)
print(f'Text: {da[0].text}')
```

```text
Text: hello world
```
````



````{tab} From Jina Hub
You can pull an Executor from Jina Hub and use it directly as a Python object. [Jina Hub](https://hub.jina.ai/) is our marketplace for Executors.

```python
from docarray import Document, DocumentArray
from jina import Executor

executor = Executor.from_hub(uri='jinahub://CLIPTextEncoder', install_requirements=True)

docs = DocumentArray(Document(text='hello'))
executor.encode(docs, {})

print(docs.embeddings.shape)
```
```text
(1, 512)
```
````

## Run async Executors


```python
import asyncio
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    async def foo(self, **kwargs):
        await asyncio.sleep(1.0)
        print(kwargs)


async def main():
    m = MyExecutor()
    call1 = asyncio.create_task(m.foo())
    call2 = asyncio.create_task(m.foo())
    await asyncio.gather(call1, call2)


asyncio.run(main())
```
