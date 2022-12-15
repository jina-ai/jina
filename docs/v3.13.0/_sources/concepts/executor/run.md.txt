# Run

You can use {class}`~jina.Executor` objects directly, just like a regular Python object.

One can instantiate an Executor object from a local Python class, or from the [Executor Hub](https://cloud.jina.ai/):

### From a local Python class

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


### From the Executor Hub
You can pull an Executor from [Executor Hub](https://cloud.jina.ai/) and use it directly as a Python object.

```python
from docarray import Document, DocumentArray
from jina import Executor

executor = Executor.from_hub(
    uri='jinaai://jina-ai/CLIPTextEncoder', install_requirements=True
)

docs = DocumentArray(Document(text='hello'))
executor.encode(docs, {})

print(docs.embeddings.shape)
```
```text
(1, 512)
```


## Run inside an async eventloop

If the Executor contains {ref}`async functions<async-executors>`, you can run it inside an asyncio eventloop.

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


## Run as a process

You can run an Executor from CLI. In this case, the Executor occupies one process. The lifetime of the Executor is the lifetime of the process.

### From a local Executor

With `exec.py` containing the definition of `MyExec`, now creating a new file called `my-exec.yml`:

```yaml
jtype: MyExec
py_modules:
  - exec.py
```

This simply points Jina to our file and Executor class. Now we can run the command:

```bash
jina executor --uses my-exec.yml --port 12345
```

### From Executor Hub

In this example, we use `CLIPTextEncoder` to create embeddings for our Documents.

````{tab} With Docker

```bash
jina executor --uses jinaai+docker://jina-ai/CLIPTextEncoder
```

````

````{tab} Without Docker

```bash
jina executor --uses jinaai://jina-ai/CLIPTextEncoder
```

````

This might take a few seconds, but in the end you should be greeted with the
following message:

```bash
WorkerRuntime@ 1[L]: Executor CLIPTextEncoder started
```

Just like that, our Executor is up and running.


