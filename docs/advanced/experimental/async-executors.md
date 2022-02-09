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
    async def encode(self,docs,*kwargs):
        await some_coroutines()
```
````



## Examples

In this example we have a heavy lifting API for which we want to call several time, we want to leverage the
async python features to speed up the `Executor`'s call by calling the api multiples times in parallel.

### With async

let's make this api call a python `coroutines`

```python
import asyncio

async def api_call(text):
    await asyncio.sleep(1)
    return text.upper()
```

and let's modify our code to leverage the non blocking api call


```python
import time
import asyncio
from docarray import Document, DocumentArray
from jina import Executor, requests, Flow

def on_done(resp):

    for doc in resp.docs:
        assert doc.text == doc.text.upper()

    results = resp.parameters['__results__']

    for res in results.values():
        print(f"the call took {res['time']} second")

class DummyAsyncExecutor(Executor):

    async def proces_doc(self, doc: Document):
        doc.text = await api_call(doc.text)

    @requests
    async def encode_async(self, docs: DocumentArray, **kwargs):

        start_time = time.time()
        task = [asyncio.ensure_future(self.proces_doc(doc)) for doc in docs]
        await asyncio.gather(*task)
        return {"time": time.time() - start_time}

f_async = Flow().add(uses=DummyAsyncExecutor)
with f_async:
    f_async.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
        on_done=test_text_value,
    )

>>>     Flow@123296[I]:🎉 Flow is ready to use!
        🔗 Protocol: 		GRPC
        🏠 Local access:	0.0.0.0:63319
        🔒 Private network:	192.168.3.50:63319
>>>     the call took 1.0029587745666504 second
```

### Without async

Here is an example without using `coroutines`, all of the 50 api calls will be queued and nothing will be done 
concurrently.

```python
def direct_api_call(text):
    time.sleep(1)
    return text.upper()


class DummyExecutor(Executor):
    
    @requests
    def encode(self, docs: DocumentArray, **kwargs):

        start_time = time.time()
        for doc in docs:
            doc.text = direct_api_call(doc.text)

        return {'time': time.time() - start_time}


f = Flow().add(uses=DummyExecutor)
with f:
    f.index(
        inputs=DocumentArray([Document(text='hello') for _ in range(50)]),
        on_done=on_done,
    )

>>>     Flow@123296[I]:🎉 Flow is ready to use!
        🔗 Protocol: 		GRPC
        🏠 Local access:	0.0.0.0:63319
        🔒 Private network:	192.168.3.50:63319
>>>     the call took 50.05074954032898 second
```


### Conclusion

The encoding of the data is 50 faster when using `coroutines` because all can happen in parallel. 











