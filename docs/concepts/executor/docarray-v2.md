(docarray-v2)=


# (Beta) Docarray-V2

Jina provide an early support  for [DocArray-v2](https://github.com/docarray/docarray/commits/feat-rewrite-v2) which
is a rewrite of DocArray.

```{warning} Beta support
DocArray v2 is  still in alpha and its support in Jina is still an experimental feature, and the API is subject to 
change.
```

## DocArray v2 schema

At the heart of DocArray v2 is a new schema that is more flexible and expressive than the original DocArray schema.

You can refer to the [DocArray v2 readme](https://github.com/docarray/docarray/tree/feat-rewrite-v2) for more details.


On Jina side this has actually quite a big impact on the spirit of how we are building Executor. Indeed, with docarray v1
the version that is currently used in Jina, the `Document` as a fixed schema and the Executor perform in place operation
on directly on it. With DocArray v2 things change slightly. Each executor will need to define its own input schema
and output schema. Of course, we still provided predefined schema. We believe this will allow Executor to be more
expressive and flexible.
expressive and flexible.

## New (Beta) Executor API

To reflect the change with DocArray v2, we have slightly extended the Executor API to support schema definition. The 
design is freely inspired by [FastAPI](https://fastapi.tiangolo.com/). 


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

For our Executor we define an input schema `InputDoc` and an output schema `OutputDoc` which are `Document`. 
We then define the `bar` endpoint which takes as input a `DocumentArray` of `InputDoc` and return a `DocumentArray` of
`OutputDoc`. Note that here the type hint is actually more that just a hint, and like in FastAPI we infer the actual
schema of the endpoint from the type hint.

There is also a way to explicitly define the schema of the endpoint. This is done by using the `input_type` and
`output_type` parameters of the `requests` decorator.


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

If there is no `input_type` and `output_type` the type hint is used to infer the schema. If there are both `input_type`
and `output_type` will be used.


## (Beta) Client API

The client will be impacted as well as we will need to provide a way to specify the schema of the data that is return 
the Executor. You can pass the return type by using the `return_type` parameter of the `client.post`

```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow

with Flow().add(uses=MyExec) as f:
    docs = f.post(
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
