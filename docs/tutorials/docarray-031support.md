(docarray-v2)=
# DocArray>0.30 support

Jina provides early support for [DocArray>=0.30](https://github.com/docarray/docarray) which
is a rewrite of DocArray. This new version makes the dataclass feature of DocArray<=0.21 a first-class citizen and for this 
purpose it is built on top of [Pydantic](https://pydantic-docs.helpmanual.io/). An important shift is that 
the new DocArray adapts to users' data, whereas DocArray<=0.21 forces user to adapt to the Document schema.

```{warning} Beta support
New DocArray syntax is available on DocArray version beyond 0.30. Not every feature in Jina has been adapted to the new DocArray versions, but some of them are.
So you can consider that the support of this new version is in Beta. The plan is to keep compatibility with 2 sets of versions after the migration 
is achieved.
```

## New DocArray schema

At the heart of DocArray>=0.30 is a new schema that is more flexible and expressive than the original DocArray schema.

You can refer to the [DocArray README](https://github.com/docarray/docarray) for more details. 
Please note that also the names of data structure change in the new version of DocArray.

On the Jina side, this flexibility extends to every Executor, where you can now customize input and output schemas:

- With DocArray<=0.21 (the version currently used by default in Jina), a Document has a fixed schema and an Executor performs in-place operations on it. 
- With DocArray>=0.30, an Executor defines its own input and output schemas. It also provides several predefined schemas that you can use out of the box.

## New Executor API

To reflect the change with DocArray >=0.30, the Executor API now supports schema definition. The 
design is inspired by [FastAPI](https://fastapi.tiangolo.com/). 


```{code-block} python
---
emphasize-lines: 17,18
---
from jina import Executor, requests
from docarray import DocList, BaseDoc
from docarray.documents import ImageDoc
from docarray.typing import AnyTensor

import numpy as np

class InputDoc(BaseDoc):
    img: ImageDoc

class OutputDoc(BaseDoc):
    embedding: AnyTensor

class MyExec(Executor):
    @requests(on='/bar')
    def bar(
        self, docs: DocList[InputDoc], **kwargs
    ) -> DocumentArray[OutputDoc]:
        docs_return = DocList[OutputDoc](
            [OutputDoc(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
        )
        return docs_return
```

For our Executor we define:

- An input schema `InputDoc` and an output schema `OutputDoc`, which are Documents. 
- The `bar` endpoint, which takes a DocumentArray of `InputDoc` as input and returns a DocumentArray of
`OutputDoc`. 

Note that the type hint is actually more that just a hint -- the Executor uses it to infer the actual
schema of the endpoint.

You can also explicitly define the schema of the endpoint by using the `request_schema` and
`response_schema` parameters of the `requests` decorator:


```{code-block} python
---
emphasize-lines: 4,5
---
class MyExec(Executor):
    @requests(
        on='/bar',
        request_schema=DocList[InputDoc],
        response_schema=DocList[OutputDoc],
    )
    def bar(self, docs, **kwargs):
        docs_return = DocList[OutputDoc](
            [OutputDoc(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
        )
        return docs_return
```

If there is no `request_schema` and `response_schema`, the type hint is used to infer the schema. If both exist, `request_schema`
and `response_schema` will be used.


## Serve one Executor in a Deployment

Once you have defined the Executor with the New Executor API, you can easily serve and scale it as a Deployment with `gRPC`, `HTTP` or any combination of these
protocols.


```{code-block} python
from jina import Deployment

with Deployment(uses=MyExec, protocol='grpc', replicas=2) as dep:
    dep.block()
```

(streaming-endpoits-docarray-v2)=
## Streaming Endpoints with DocArray >=0.30
Similarly to {ref}`Streaming Endpoints API <streaming-endpoints>` in DocArray V1, you can implement streaming endpoints 
with DocArray >=0.30 schemas.

Streaming endpoints receive one Document as input and yields one Document at a time.

A streaming endpoint has the following signature:

```python
from jina import Executor, requests, Document, Deployment

# first define schemas
class MyDocument(Document):
    text: str

# then define the Executor
class MyExecutor(Executor):

    @requests(on='/hello')
    async def task(self, doc: MyDocument, **kwargs):
        print()
        # for doc in docs:
        #     doc.text = 'hello world'
        for i in range(100):
            yield MyDocument(text=f'hello world {i}')
            
with Deployment(
    uses=MyExecutor,
    port=12345,
    protocol='http',
    cors=True,
    include_gateway=False,
) as dep:
    dep.block()
```

From the client side, any SSE client can be used to receive the Documents, one at a time.
Jina's standard python client also supports streaming endpoints with DocArray >=0.30:

```python
from jina import Client, Document
client = Client(port=12345, protocol='http', cors=True, asyncio=True)
async for doc in client.stream_doc(
    on='/hello', inputs=MyDocument(text='hello world'), return_type=MyDocument
):
    print(doc.text)
```
```text
hello world 0
hello world 1
hello world 2
```

## Compatible features

Jina is working to offer full compatibility with the new DocArray version.

However, there are currently some limitations to consider.


````{admonition} Note
:class: note

With DocArray 0.30 support, Jina introduced the concept of input/output schema at the Executor level. To chain multiple Executors into a Flow you need to ensure that the output schema of an Executor is the same as the input of the Executor that follows it in the Flow
````

````{admonition} Note
:class: note

For now, [Executor Hub](https://cloud.jina.ai/executors] will not automatically build your Docker images with the new DocArray version. If this is needed, you need to provide your 
Dockerfile where `docarray>=0.30` is specifically installed.

````


## See also

- [DocArray >0.30](https://github.com/docarray/docarray) README
- [Pydantic](https://pydantic-docs.helpmanual.io/) documentation for more details on the schema definition

