from typing import Optional
import pytest
import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import ImageDoc
from docarray.typing import AnyTensor, ImageUrl
from jina.helper import random_port

from jina import Deployment, Executor, Flow, requests, Client


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['grpc', 'http']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_different_document_schema(protocols, replicas):
    if 'http' in protocols:
        return

    class Image(BaseDoc):
        tensor: Optional[AnyTensor]
        url: ImageUrl

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocList[Image], **kwargs) -> DocList[Image]:
            for doc in docs:
                doc.tensor = doc.url.load()
            return docs

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec) as f:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/foo',
                inputs=DocList[Image]([Image(url='https://via.placeholder.com/150.png')]),
                return_type=DocList[Image],
            )
            docs = docs.to_doc_vec()
            assert docs.tensor.ndim == 4


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['grpc', 'http']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_send_custom_doc(protocols, replicas):
    if 'http' in protocols:
        return

    class MyDoc(BaseDoc):
        text: str

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocList[MyDoc], **kwargs):
            docs[0].text = 'hello world'

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec) as f:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(on='/foo', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
            assert docs[0].text == 'hello world'


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['grpc', 'http']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_input_response_schema(protocols, replicas):
    if 'http' in protocols:
        return

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

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec) as f:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(on='/foo', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
            assert docs[0].text == 'hello world'
            assert docs.__class__.doc_type == MyDoc


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['grpc', 'http']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_input_response_schema_annotation(protocols, replicas):
    if 'http' in protocols:
        return

    class MyDoc(BaseDoc):
        text: str

    class MyExec(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
            assert docs.__class__.doc_type == MyDoc
            docs[0].text = 'hello world'
            return docs

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec) as f:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(on='/bar', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
            assert docs[0].text == 'hello world'
            assert docs.__class__.doc_type == MyDoc


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['grpc', 'http']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_different_output_input(protocols, replicas):
    if 'http' in protocols:
        return

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

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec) as f:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/bar',
                inputs=InputDoc(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
                return_type=DocList[OutputDoc],
            )
            assert docs[0].embedding.shape == (100, 1)
            assert docs.__class__.doc_type == OutputDoc


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['grpc', 'http']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_deployments(protocols, replicas):
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
   
    ports = [random_port() for _ in protocols]
    with Deployment(port=ports, protocol=protocols, replicas=replicas, uses=MyExec) as dep:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
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
            for q in docs:
                res = ResultTestDoc(id=q.id, matches=self._docs[0:3])
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
