(docker-compose)=
# Using async python within Executors


One of the most exciting feature that come with Jina 3 is the ability to naturally call async coroutines within 
executors, allowing you to leverage the power of asynchronous python to write concurrent code. 

`Executor`'s are not only static code, but they live within a `Flow`
as a microservices waiting for `DocumentArray` to flow through (i.e. be passed to) them. In jina 2 this feature was 
not possible because the inner python loop in which `Executor`'s were living was not compatible with the async loop.
In Jina 3 we completely redesign this inner loop to be compatible with async python. 


## Examples

## Simplest async call

First lets define a simple coroutine 

```python
import asyncio

async def api_call():
    await asyncio.sleep(1)
    return "hello world"
```
Now we call it from an `Executors`

```python
from jina import Executor,requests,Flow
from docarray import Document,DocumentArray

class DummyAsyncExecutor(Executor):
    
    @requests
    def encode(self, docs : DocumentArray, **kwargs):
        
        value = asyncio.run(api_call())
        
        for doc in docs:
            doc.text = value
```

let's try to run it in a `Flow`

```python
f = Flow().add(uses=DummyAsyncExecutor)

def test_text_value(resp):
    
    for doc in resp.docs:
       assert doc.text == "hello world"

with f:
    f.search(inputs=DocumentArray([Document(text="")]),on_done=test_text_value)
```

## Async with Executor in practice

let's define

