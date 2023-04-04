from typing import Optional

import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import ImageDoc
from docarray.typing import AnyTensor, ImageUrl

from jina import Deployment, Executor, Flow, requests


def test_different_document_schema():
    class Image(BaseDoc):
        tensor: Optional[AnyTensor]
        url: ImageUrl

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocList[Image], **kwargs) -> DocList[Image]:
            for doc in docs:
                doc.tensor = doc.url.load()
            return docs

    with Flow().add(uses=MyExec) as f:
        docs = f.post(
            on='/foo',
            inputs=DocList[Image]([Image(url='https://via.placeholder.com/150.png')]),
            return_type=DocList[Image],
        )
        docs = docs.stack()
        assert docs.tensor.ndim == 4


def test_send_custom_doc():
    class MyDoc(BaseDoc):
        text: str

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocList[MyDoc], **kwargs):
            docs[0].text = 'hello world'

    with Flow().add(uses=MyExec) as f:
        doc = f.post(on='/foo', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
        assert doc[0].text == 'hello world'


def test_input_response_schema():
    class MyDoc(BaseDoc):
        text: str

    class MyExec(Executor):
        @requests(
            on='/foo',
            request_schema=DocList[MyDoc],
            response_schema=DocList[MyDoc],
        )
        def foo(self, docs, **kwargs):
            assert docs.__class__.doc_type == MyDoc
            docs[0].text = 'hello world'
            return docs

    with Flow().add(uses=MyExec) as f:
        docs = f.post(on='/foo', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
        assert docs[0].text == 'hello world'
        assert docs.__class__.doc_type == MyDoc


def test_input_response_schema_annotation():
    class MyDoc(BaseDoc):
        text: str

    class MyExec(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
            assert docs.__class__.doc_type == MyDoc
            docs[0].text = 'hello world'
            return docs

    with Flow().add(uses=MyExec) as f:
        docs = f.post(on='/bar', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
        assert docs[0].text == 'hello world'
        assert docs.__class__.doc_type == MyDoc


def test_different_output_input():
    class InputDoc(BaseDoc):
        img: ImageDoc

    class OutputDoc(BaseDoc):
        embedding: AnyTensor

    class MyExec(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[InputDoc], **kwargs) -> DocList[OutputDoc]:
            docs_return = DocList[OutputDoc](
                [OutputDoc(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
            )
            return docs_return

    with Flow().add(uses=MyExec) as f:
        docs = f.post(
            on='/bar',
            inputs=InputDoc(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
            return_type=DocList[OutputDoc],
        )
        assert docs[0].embedding.shape == (100, 1)
        assert docs.__class__.doc_type == OutputDoc


def test_deployments():
    class InputDoc(BaseDoc):
        img: ImageDoc

    class OutputDoc(BaseDoc):
        embedding: AnyTensor

    class MyExec(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[InputDoc], **kwargs) -> DocList[OutputDoc]:
            docs_return = DocList[OutputDoc](
                [OutputDoc(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
            )
            return docs_return

    with Deployment(uses=MyExec) as dep:
        docs = dep.post(
            on='/bar',
            inputs=InputDoc(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
            return_type=DocList[OutputDoc],
        )
        assert docs[0].embedding.shape == (100, 1)
        assert docs.__class__.doc_type == OutputDoc
