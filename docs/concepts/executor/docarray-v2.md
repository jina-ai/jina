(docarray-v2)=


# (Beta) DocArray v2

Jina provides early support for [DocArray v2](https://github.com/docarray/docarray/commits/feat-rewrite-v2) which
is a rewrite of DocArray. DocArray v2 makes the dataclass feature of DocArray-v1 a first-class citizen and for this 
purpose it is built on top of [pydantic](https://pydantic-docs.helpmanual.io/) and . An important shift is that 
DocArray v2 adapts to users' data, whereas DocArray v1 forces user to adapt to the Document schema.

```{warning} Beta support
DocArray v2 is  still in alpha, its support in Jina is still an experimental feature, and the API is subject to 
change.
```

## DocArray v2 schema

At the heart of DocArray v2 is a new schema that is more flexible and expressive than the original DocArray schema.

You can refer to the [DocArray v2 readme](https://github.com/docarray/docarray/tree/feat-rewrite-v2) for more details.


On the Jina side, this flexibility extends to every Executor, where you can now customize input and output schemas

- With DocArray v1 (the version currently used in Jina), a Document has a fixed schema and an Executor performs in-place operations on it. 
- With DocArray v2, an Executor defines its own input and output schemas. It also provides several predefined schemas that you can use out of the box.

## (Beta) New Executor API

To reflect the change with DocArray v2, the Executor API now supports schema definition. The 
design is inspired by [FastAPI](https://fastapi.tiangolo.com/). 


```{code-block} python
---
emphasize-lines: 17,18
---
from jina import Executor, requests
from docarray import BaseDocument, DocumentArray
from docarray.documents import Image
from docarray.typing import AnyTensor

import numpy as np

class InputDoc(BaseDocument):
    img: Image

class OutputDoc(BaseDocument):
    embedding: AnyTensor

class MyExec(Executor):
    @requests(on='/bar')
    def bar(
        self, docs: DocumentArray[InputDoc], **kwargs
    ) -> DocumentArray[OutputDoc]:
        docs_return = DocumentArray[OutputDoc](
            [OutputDoc(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
        )
        return docs_return
```

For our Executor we define:

- An input schema `InputDoc` and an output schema `OutputDoc`, which are Documents. 
- The `bar` endpoint which takes as input a DocumentArray of `InputDoc` and returns a DocumentArray of
`OutputDoc`. 

Note that here the type hint is actually more that just a hint -- the Executor uses it to infer the actual
schema of the endpoint.

You can also explicitly define the schema of the endpoint by using the `input_type` and
`output_type` parameters of the `requests` decorator:


```{code-block} python
---
emphasize-lines: 4,5
---
class MyExec(Executor):
    @requests(
        on='/bar',
        input_type=DocumentArray[InputDoc],
        output_type=DocumentArray[OutputDoc],
    )
    def bar(self, docs, **kwargs) 
        docs_return = DocumentArray[OutputDoc](
            [OutputDoc(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
        )
        return docs_return
```

If there is no `input_type` and `output_type` the type hint is used to infer the schema. If both exist, `input_type`
and `output_type` will be used.


## (Beta) Client API

In the client, you similarly specify the schema that you expect the Flow to return. You can pass the return type by using the `return_type` parameter of the `client.post`

```{code-block} python
---
emphasize-lines: 7
---
from jina import Deployment

with Deployment(uses=MyExec) as dep:
    docs = dep.post(
        on='/bar',
        inputs=InputDoc(img=Image(tensor=np.zeros((3, 224, 224)))),
        return_type=DocumentArray[OutputDoc],
    )
    assert docs[0].embedding.shape == (100, 1)
    assert docs.__class__.document_type == OutputDoc
```



```{note}

## See further

- [DocArray-v2](https://github.com/docarray/docarray/commits/feat-rewrite-v2) readme
- [Pydantic](https://pydantic-docs.helpmanual.io/) documentation for more details on the schema definition

```
