(async-executors)=
# Using async python within Executors


You can naturally call async coroutines within `Executor`'s, allowing you to leverage the power of asynchronous
Python to write concurrent code. 


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

In this example we have a heavy lifting API for which we want to call several times, we want to leverage the
async Python features to speed up the `Executor`'s call by calling the api multiples times concurrently.

### With async


```python
import time
import asyncio
from docarray import Document, DocumentArray
from jina import Executor, requests, Flow

class DummyAsyncExecutor(Executor):
   @requests
   async def encode(self, docs: DocumentArray, **kwargs): 
         await asyncio.sleep(1)
         for doc in docs:
            doc.text = doc.text.upper()


f = Flow().add(uses=DummyAsyncExecutor)

with f:
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
        request_size=1,
        show_progress=True
    )
    
print(f"Processing took {time.time()-start_time} seconds")
>>>     Flow@123296[I]:🎉 Flow is ready to use!
        🔗 Protocol: 		GRPC
        🏠 Local access:	0.0.0.0:63319
⠙       DONE ━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:01 100% ETA: 0 seconds 41 steps done in 1 second
```

### Without async

Here is an example without using `coroutines`, all of the 50 api calls will be queued and nothing will be done 
concurrently.

```python

class DummyExecutor(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        time.sleep(1)
        for doc in docs:
            doc.text = doc.text.upper()

f = Flow().add(uses=DummyExecutor)

with f:
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
        request_size=1,
        show_progress=True
    )
>>>     Flow@123296[I]:🎉 Flow is ready to use!
        🔗 Protocol: 		GRPC
        🏠 Local access:	0.0.0.0:63319
⠸       DONE ━━━━━━━━━━━━━━━━━━━━╸━━━━━━━━━━━━━━━━━━━━ 0:00:02 100% ETA: 0 seconds 41 steps done in 50 seconds
```


### Conclusion

The processing of the data is 50 faster when using `coroutines` because it happens concurrently.










