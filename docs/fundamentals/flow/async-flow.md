# Asynchronous Flow

`AsyncFlow` is an "async version" of the `Flow` class.

The quote mark represents the explicit async when using `AsyncFlow`.

While synchronous from outside, `Flow` also runs asynchronously under the hood: it manages the eventloop(s) for
scheduling the jobs. If the user wants more control over the eventloop, then `AsyncFlow` can be used.


## Create AsyncFlow

To create an `AsyncFlow`, simply

```python
from jina import AsyncFlow

f = AsyncFlow()
```

There is also a sugary syntax `Flow(asyncio=True)` for initiating an `AsyncFlow` object.

```python
from jina import Flow

f = Flow(asyncio=True)
```

## Input & output

Unlike `Flow`, `AsyncFlow` accepts input and output functions
as [async generators](https://www.python.org/dev/peps/pep-0525/). This is useful when your data sources involve other
asynchronous libraries (e.g. motor for MongoDB):

```python
import asyncio

from jina import AsyncFlow, Document


async def async_inputs():
    for _ in range(10):
        yield Document()
        await asyncio.sleep(0.1)


with AsyncFlow().add() as f:
    async for resp in f.post('/', async_inputs):
        print(resp)
```

## Using AsyncFlow for overlapping heavy-lifting job

`AsyncFlow` is particularly useful when Jina and another heavy-lifting job are running concurrently:

```python
import time
import asyncio

from jina import AsyncFlow, Executor, requests


class HeavyWork(Executor):

    @requests
    def foo(self, **kwargs):
        time.sleep(5)


async def run_async_flow_5s():
    with AsyncFlow().add(uses=HeavyWork) as f:
        async for resp in f.post('/'):
            print(resp)


async def heavylifting():  # total roundtrip takes ~5s
    print('heavylifting other io-bound jobs, e.g. download, upload, file io')
    await asyncio.sleep(5)
    print('heavylifting done after 5s')


async def concurrent_main():  # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
    await asyncio.gather(run_async_flow_5s(), heavylifting())


if __name__ == '__main__':
    asyncio.run(concurrent_main())
```

`AsyncFlow` is very useful when using Jina inside a Jupyter Notebook, where it can run out-of-the-box.
