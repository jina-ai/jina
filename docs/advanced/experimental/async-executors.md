(docker-compose)=
# Using async python within Executors


You can use naturally call async coroutines within `Executor`'s, allowing you to leverage the power of asynchronous
python to write concurrent code. 


````{admonition} Example code
:class: tip

Functions decorated by `requests`  can be directly implemented as async `coroutines. 

```python
from jina import Executor, requests, Flow

class MyExecutor(Executor):
    
    @requests
    async def encode(self, docs, *kwargs):
        await some_coroutines()
```
````

## Examples

In this example we have a heavy lifting API for which we want to call several time, we want to leverage the
async python features to speed up the `Executor`'s call by calling the api multiples times in parallel.

### With async


```python
import time
import asyncio
from docarray import Document, DocumentArray
from jina import Executor, requests, Flow

class DummyAsyncExecutor(Executor):
    @requests
    async def encode_async(self, docs: DocumentArray, **kwargs):
        async def proces_doc(doc):
            await asyncio.sleep(1)
            doc.text = doc.text.upper()

        await asyncio.gather(*[proces_doc(doc) for doc in docs])


f = Flow().add(uses=DummyAsyncExecutor)

with f:

    start_time = time.time()
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
    )
    
print(f"the call took {time.time()-start_time} second")

>>>     Flow@123296[I]:🎉 Flow is ready to use!
        🔗 Protocol: 		GRPC
        🏠 Local access:	0.0.0.0:63319
>>>     the call took 1.0029587745666504 second
```

### Without async

Here is an example without using `coroutines`, all of the 50 api calls will be queued and nothing will be done 
concurrently.

```python

class DummyExecutor(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs):

        for doc in docs:
            time.sleep(1)
            doc.text = doc.text.upper()



f = Flow().add(uses=DummyExecutor)

with f:
    start_time = time.time()
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(2)]),
    )
    
print(f"the call took {time.time()-start_time} second")

>>>     Flow@123296[I]:🎉 Flow is ready to use!
        🔗 Protocol: 		GRPC
        🏠 Local access:	0.0.0.0:63319
>>>     the call took 50.05074954032898 second
```


### Conclusion

The encoding of the data is 50 faster when using `coroutines` because all can happen in parallel. 











