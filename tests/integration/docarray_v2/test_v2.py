from typing import Optional

import numpy as np
from docarray import BaseDocument, DocumentArray
from docarray.documents import ImageDoc
from docarray.typing import AnyTensor, ImageUrl

from jina import Deployment, Executor, Flow, requests


def test_different_document_schema():
    class Image(BaseDocument):
        tensor: Optional[AnyTensor]
        url: ImageUrl

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocumentArray[Image], **kwargs) -> DocumentArray[Image]:
            for doc in docs:
                doc.tensor = doc.url.load()
            return docs

    with Flow().add(uses=MyExec) as f:
        docs = f.post(
            on='/foo',
            inputs=DocumentArray[Image](
                [Image(url='https://via.placeholder.com/150.png')]
            ),
            return_type=DocumentArray[Image],
        )
        docs = docs.stack()
        assert docs.tensor.ndim == 4


def test_send_custom_doc():
    class MyDoc(BaseDocument):
        text: str

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocumentArray[MyDoc], **kwargs):
            docs[0].text = 'hello world'

    with Flow().add(uses=MyExec) as f:
        doc = f.post(
            on='/foo', inputs=MyDoc(text='hello'), return_type=DocumentArray[MyDoc]
        )
        assert doc[0].text == 'hello world'


def test_input_response_schema():
    class MyDoc(BaseDocument):
        text: str

    class MyExec(Executor):
        @requests(
            on='/foo',
            request_schema=DocumentArray[MyDoc],
            response_schema=DocumentArray[MyDoc],
        )
        def foo(self, docs, **kwargs):
            assert docs.__class__.document_type == MyDoc
            docs[0].text = 'hello world'
            return docs

    with Flow().add(uses=MyExec) as f:
        docs = f.post(
            on='/foo', inputs=MyDoc(text='hello'), return_type=DocumentArray[MyDoc]
        )
        assert docs[0].text == 'hello world'
        assert docs.__class__.document_type == MyDoc


def test_input_response_schema_annotation():
    class MyDoc(BaseDocument):
        text: str

    class MyExec(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocumentArray[MyDoc], **kwargs) -> DocumentArray[MyDoc]:
            assert docs.__class__.document_type == MyDoc
            docs[0].text = 'hello world'
            return docs

    with Flow().add(uses=MyExec) as f:
        docs = f.post(
            on='/bar', inputs=MyDoc(text='hello'), return_type=DocumentArray[MyDoc]
        )
        assert docs[0].text == 'hello world'
        assert docs.__class__.document_type == MyDoc


def test_different_output_input():
    class InputDoc(BaseDocument):
        img: ImageDoc

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

    with Flow().add(uses=MyExec) as f:
        docs = f.post(
            on='/bar',
            inputs=InputDoc(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
            return_type=DocumentArray[OutputDoc],
        )
        assert docs[0].embedding.shape == (100, 1)
        assert docs.__class__.document_type == OutputDoc


def test_deployments():
    class InputDoc(BaseDocument):
        img: ImageDoc

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

    with Deployment(uses=MyExec) as dep:
        docs = dep.post(
            on='/bar',
            inputs=InputDoc(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
            return_type=DocumentArray[OutputDoc],
        )
        assert docs[0].embedding.shape == (100, 1)
        assert docs.__class__.document_type == OutputDoc
