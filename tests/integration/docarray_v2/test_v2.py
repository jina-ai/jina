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
        docs = docs.to_doc_vec()
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


def test_deployments_with_shards_one_shard_fails():
    from docarray.documents import TextDoc
    from docarray import DocList, BaseDoc

    class TextDocWithId(TextDoc):
        id: str

    class KVTestIndexer(Executor):
        """Simulates an indexer where one shard would fail"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._docs_dict = {}

        @requests(on=['/index'])
        def index(self, docs: DocList[TextDocWithId], **kwargs) -> DocList[TextDocWithId]:
            for doc in docs:
                self._docs_dict[doc.id] = doc

        @requests(on=['/search'])
        def search(self, docs: DocList[TextDocWithId], **kwargs) -> DocList[TextDocWithId]:
            for doc in docs:
                doc.text = self._docs_dict[doc.id].text

    with Deployment(uses=KVTestIndexer, shards=2) as dep:
        index_da = DocList[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        dep.index(inputs=index_da, request_size=1, return_type=DocList[TextDocWithId])
        responses = dep.search(inputs=index_da, request_size=1, return_type=DocList[TextDocWithId])
        for q, r in zip(index_da, responses):
            assert q.text == r.text


def test_deployments_with_shards_all_shards_return():
    from docarray.documents import TextDoc
    from docarray import DocList, BaseDoc

    class TextDocWithId(TextDoc):
        id: str

    class ResultTestDoc(BaseDoc):
        matches: DocList[TextDocWithId]

    class SimilarityTestIndexer(Executor):
        """Simulates an indexer where no shard would fail, they all pass results"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._docs = DocList[TextDocWithId]()

        @requests(on=['/index'])
        def index(self, docs: DocList[TextDocWithId], **kwargs) -> DocList[TextDocWithId]:
            for doc in docs:
                self._docs.append(doc)

        @requests(on=['/search'])
        def search(self, docs: DocList[TextDocWithId], **kwargs) -> DocList[ResultTestDoc]:
            resp = DocList[ResultTestDoc]()
            for _ in docs:
                res = ResultTestDoc(matches=self._docs[0:3])
                resp.append(res)
            return resp

    with Deployment(uses=SimilarityTestIndexer, shards=2) as dep:
        index_da = DocList[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(10)]
        )
        dep.index(inputs=index_da, request_size=1, return_type=DocList[TextDocWithId])
        import time
        time.sleep(2)
        responses = dep.search(inputs=index_da[0:1], request_size=1, return_type=DocList[ResultTestDoc])
        for r in responses:
            assert len(r.matches) == 6
