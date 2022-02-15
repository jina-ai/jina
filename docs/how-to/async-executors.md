(async-executors)=
# How to use async coroutines in Executors


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

In this example we have a heavy lifting API for which we want to call several times, and we want to leverage the
async Python features to speed up the `Executor`'s call by calling the API multiples times concurrently.

### With async


```python
import asyncio

from docarray import Document, DocumentArray
from jina import Flow, Executor, requests


class DummyAsyncExecutor(Executor):
    @requests
    async def process(self, docs: DocumentArray, **kwargs):
        await asyncio.sleep(1)
        for doc in docs:
            doc.text = doc.text.upper()


f = Flow().add(uses=DummyAsyncExecutor)

with f:
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
        request_size=1,
        show_progress=True,
    )
```

```console
           Flow@20588[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:62598
	🔒 Private network:	192.168.1.187:62598
	🌐 Public address:	212.231.186.65:62598
⠙       DONE ━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:01 100% ETA: 0 seconds 41 steps done in 1 second
```

### Without async

Here is an example without using `coroutines`. All of the 50 API calls will be queued and nothing will be done 
concurrently.

```python
import time

from docarray import DocumentArray, Document
from jina import Flow, Executor, requests


class DummyExecutor(Executor):
    @requests
    def process(self, docs: DocumentArray, **kwargs):
        time.sleep(1)
        for doc in docs:
            doc.text = doc.text.upper()


f = Flow().add(uses=DummyExecutor)

with f:
    f.index(
        inputs=DocumentArray([Document(text="hello") for _ in range(50)]),
        request_size=1,
        show_progress=True,
    )
```

```console
           Flow@20394[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:52592
	🔒 Private network:	192.168.1.187:52592
	🌐 Public address:	212.231.186.65:52592
⠏       DONE ━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:50 100% ETA: 0 seconds 41 steps done in 50 seconds
```


### Conclusion

The processing of the data is 50 faster when using `coroutines` because it happens concurrently.
