from typing import Optional, List, Dict, Union
import pytest
import time
import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import ImageDoc
from docarray.typing import AnyTensor, ImageUrl
from docarray.documents import TextDoc
from jina.helper import random_port

from jina import Deployment, Executor, Flow, requests, Client


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_different_document_schema(protocols, replicas):
    class Image(BaseDoc):
        tensor: Optional[AnyTensor]
        url: ImageUrl
        lll: List[List[str]] = [[]]
        texts: DocList[TextDoc]

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocList[Image], **kwargs) -> DocList[Image]:
            for doc in docs:
                doc.tensor = np.zeros((10, 10, 10))
                doc.lll = [['aa'], ['bb']]
                doc.texts.append(TextDoc('ha'))
            return docs

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec) as f:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/foo',
                inputs=DocList[Image](
                    [Image(url='https://via.placeholder.com/150.png', texts=DocList[TextDoc]([TextDoc('hey')]))]),
                return_type=DocList[Image],
            )
            docs = docs.to_doc_vec()
            assert docs.tensor.ndim == 4
            assert docs[0].lll == [['aa'], ['bb']]
            assert len(docs[0].texts) == 2
            assert docs[0].texts[0].text == 'hey'
            assert docs[0].texts[1].text == 'ha'


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_send_custom_doc(protocols, replicas):
    class MyDoc(BaseDoc):
        text: str

    class MyExec(Executor):
        @requests(on='/foo')
        def foo(self, docs: DocList[MyDoc], **kwargs):
            docs[0].text = 'hello world'

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(on='/foo', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
            assert docs[0].text == 'hello world'


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_input_response_schema(protocols, replicas):
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
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(on='/foo', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
            assert docs[0].text == 'hello world'
            assert docs.__class__.doc_type == MyDoc


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_input_response_schema_annotation(protocols, replicas):
    class MyDoc(BaseDoc):
        text: str

    class MyExec(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
            assert docs.__class__.doc_type == MyDoc
            docs[0].text = 'hello world'
            return docs

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(on='/bar', inputs=MyDoc(text='hello'), return_type=DocList[MyDoc])
            assert docs[0].text == 'hello world'
            assert docs.__class__.doc_type == MyDoc


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
@pytest.mark.parametrize('replicas', [1, 3])
def test_different_output_input(protocols, replicas):
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
    with Flow(port=ports, protocol=protocols, replicas=replicas).add(uses=MyExec):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/bar',
                inputs=InputDoc(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
                return_type=DocList[OutputDoc],
            )
            assert docs[0].embedding.shape == (100, 1)
            assert docs.__class__.doc_type == OutputDoc


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
def test_chain(protocols):
    class Input1(BaseDoc):
        img: ImageDoc

    class Output1(BaseDoc):
        embedding: AnyTensor

    class Output2(BaseDoc):
        a: str

    class Exec1(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[Input1], **kwargs) -> DocList[Output1]:
            docs_return = DocList[Output1](
                [Output1(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
            )
            return docs_return

    class Exec2(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[Output1], **kwargs) -> DocList[Output2]:
            docs_return = DocList[Output2](
                [Output2(a=f'shape input {docs[0].embedding.shape[0]}') for _ in range(len(docs))]
            )
            return docs_return

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols).add(uses=Exec1).add(uses=Exec2):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/bar',
                inputs=Input1(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
                return_type=DocList[Output2],
            )
            assert len(docs) == 1
            assert docs[0].a == 'shape input 100'


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
def test_default_endpoint(protocols):
    # TODO: Test how it behaves with complex topologies and filtering
    class Input1(BaseDoc):
        img: ImageDoc

    class Output1(BaseDoc):
        embedding: AnyTensor

    class Output2(BaseDoc):
        a: str

    class Exec1(Executor):
        @requests()
        def bar(self, docs: DocList[Input1], **kwargs) -> DocList[Output1]:
            docs_return = DocList[Output1](
                [Output1(embedding=np.zeros((100, 1))) for _ in range(len(docs))]
            )
            return docs_return

    class Exec2(Executor):
        @requests()
        def bar(self, docs: DocList[Output1], **kwargs) -> DocList[Output2]:
            docs_return = DocList[Output2](
                [Output2(a=f'shape input {docs[0].embedding.shape[0]}') for _ in range(len(docs))]
            )
            return docs_return

    ports = [random_port() for _ in protocols]
    with Flow(port=ports, protocol=protocols).add(uses=Exec1).add(uses=Exec2):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/default',
                inputs=Input1(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
                return_type=DocList[Output2],
            )
            assert len(docs) == 1
            assert docs[0].a == 'shape input 100'


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
@pytest.mark.parametrize('reduce', [True, False])
def test_complex_topology_bifurcation(protocols, reduce):
    # TODO: Test how it behaves with complex topologies where bifurcation and reduction occur
    class DocTest(BaseDoc):
        text: str

    class ExecutorTest(Executor):
        def __init__(self, text, **kwargs):
            super().__init__(**kwargs)
            self.text = text

        @requests
        def endpoint(self, docs: DocList[DocTest], **kwargs) -> DocList[DocTest]:
            for doc in docs:
                doc.text = self.text

    class ReduceExecutorTest(Executor):

        @requests
        def endpoint(self, docs: DocList[DocTest], **kwargs) -> DocList[DocTest]:
            return docs

    ports = [random_port() for _ in protocols]
    flow = (
        Flow(protocol=protocols, port=ports)
            .add(uses=ExecutorTest, uses_with={'text': 'exec1'}, name='pod0')
            .add(uses=ExecutorTest, uses_with={'text': 'exec2'}, needs='gateway', name='pod1')
            .add(uses=ExecutorTest, uses_with={'text': 'exec3'}, needs='gateway', name='pod2')
            .add(needs=['pod0', 'pod1', 'pod2'], uses=ReduceExecutorTest, no_reduce=not reduce, name='pod3')
    )

    with flow:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post('/', inputs=DocList[DocTest]([DocTest(text='') for _ in range(5)]),
                          return_type=DocList[DocTest])
            assert len(docs) == 5 if reduce else 15
            for doc in docs:
                assert 'exec' in doc.text


@pytest.fixture()
def temp_workspace(tmpdir):
    import os
    os.environ['TEMP_WORKSPACE'] = str(tmpdir)
    yield
    os.unsetenv('TEMP_WORKSPACE')


@pytest.mark.parametrize('protocol', ['grpc'])
def test_condition_feature(protocol, temp_workspace, tmpdir):
    # TODO: Test how it behaves with complex topologies and filtering
    import os

    class ProcessingTestDocConditions(BaseDoc):
        text: str
        tags: Dict[str, int]

    class ConditionDumpExecutor(Executor):
        @requests(on='/bar')
        def foo(self, docs: DocList[ProcessingTestDocConditions], **kwargs) -> DocList[ProcessingTestDocConditions]:
            with open(
                    os.path.join(str(self.workspace), f'{self.metas.name}.txt'), 'w', encoding='utf-8'
            ) as fp:
                for doc in docs:
                    fp.write(doc.text)
                    doc.text += f' processed by {self.metas.name}'

    f = (
        Flow(protocol=protocol)
            .add(name='first')
            .add(
            uses=ConditionDumpExecutor,
            uses_metas={'name': 'exec1'},
            workspace=os.environ['TEMP_WORKSPACE'],
            name='exec1',
            needs=['first'],
            when={'tags__type': {'$eq': 1}})
            .add(
            uses=ConditionDumpExecutor,
            workspace=os.environ['TEMP_WORKSPACE'],
            uses_metas={'name': 'exec2'},
            name='exec2',
            needs='first',
            when={'tags__type': {'$gt': 1}})
            .needs_all('joiner')
    )

    with f:
        input_da = DocList[ProcessingTestDocConditions](
            [ProcessingTestDocConditions(text='type1', tags={'type': 1}),
             ProcessingTestDocConditions(text='type2', tags={'type': 2})])

        ret = f.post(
            on='/bar',
            inputs=input_da,
            return_type=DocList[ProcessingTestDocConditions],
        )
        assert len(ret) == 2
        types_set = set()
        for doc in ret:
            if doc.tags['type'] == 1:
                assert doc.text == 'type1 processed by exec1'
            else:
                assert doc.tags['type'] == 2
                assert doc.text == 'type2 processed by exec2'
            types_set.add(doc.tags['type'])

        assert types_set == {1, 2}

        with open(os.path.join(str(tmpdir), 'exec1', '0', f'exec1.txt'), 'r', encoding='utf-8') as fp:
            assert fp.read() == 'type1'

        with open(os.path.join(str(tmpdir), 'exec2', '0', f'exec2.txt'), 'r', encoding='utf-8') as fp:
            assert fp.read() == 'type2'


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
def test_endpoints_target_executors_combinations(protocols):
    # TODO: Test how it behaves with complex topologies and filtering
    pass


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
def test_floating_executors(protocols):
    # TODO: Test how it behaves with complex topologies and filtering
    pass


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
    with Deployment(port=ports, protocol=protocols, replicas=replicas, uses=MyExec):
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
def test_deployments_complex_model(protocols, replicas):
    class InputDoc(BaseDoc):
        img: ImageDoc

    class OutputDoc(BaseDoc):
        tensor: Optional[AnyTensor]
        url: ImageUrl
        lll: List[List[List[int]]] = [[[5]]]
        fff: List[List[List[float]]] = [[[5.2]]]
        single_text: TextDoc
        texts: DocList[TextDoc]
        d: Dict[str, str] = {'a': 'b'}
        u: Union[str, int]
        lu: List[Union[str, int]] = [0, 1, 2]

    class MyExec(Executor):
        @requests(on='/bar')
        def bar(self, docs: DocList[InputDoc], **kwargs) -> DocList[OutputDoc]:
            docs_return = DocList[OutputDoc](
                [OutputDoc(url='photo.jpg', lll=[[[40]]], fff=[[[40.2]]], d={'b': 'a'},
                           texts=DocList[TextDoc]([TextDoc(text='hey ha', embedding=np.zeros(3))]),
                           single_text=TextDoc(text='single hey ha', embedding=np.zeros(2)), u='a', lu=[3, 4]) for _ in
                 range(len(docs))]
            )
            return docs_return

    ports = [random_port() for _ in protocols]
    with Deployment(port=ports, protocol=protocols, replicas=replicas, uses=MyExec):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/bar',
                inputs=InputDoc(img=ImageDoc(tensor=np.zeros((3, 224, 224)))),
                return_type=DocList[OutputDoc],
            )
            assert docs[0].url == 'photo.jpg'
            assert docs[0].lll == [[[40]]]
            assert docs[0].fff == [[[40.2]]]
            assert docs[0].d == {'b': 'a'}
            assert docs[0].u == 'a'
            assert docs[0].lu == ['3', '4']
            assert len(docs[0].texts) == 1
            assert docs[0].single_text.text == 'single hey ha'
            assert docs[0].single_text.embedding.shape == (2,)
            assert len(docs[0].texts) == 1
            assert docs[0].texts[0].text == 'hey ha'
            assert docs[0].texts[0].embedding.shape == (3,)


def test_deployments_with_shards_one_shard_fails():
    from docarray.documents import TextDoc
    from docarray import DocList

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


@pytest.mark.parametrize('reduce', [True, False])
@pytest.mark.parametrize('sleep_time', [0.1, 5])
def test_deployments_with_shards_all_shards_return(reduce, sleep_time):
    from docarray.documents import TextDoc
    from docarray import DocList, BaseDoc
    from typing import List

    class TextDocWithId(TextDoc):
        id: str
        l: List[int] = []

    class ResultTestDoc(BaseDoc):
        price: int = '2'
        l: List[int] = [3]
        matches: DocList[TextDocWithId]

    class SimilarityTestIndexer(Executor):
        """Simulates an indexer where no shard would fail, they all pass results"""

        def __init__(self, sleep_time=0.1, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._docs = DocList[TextDocWithId]()
            time.sleep(sleep_time)

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

    with Deployment(uses=SimilarityTestIndexer, uses_with={'sleep_time': sleep_time}, shards=2, reduce=reduce) as dep:
        index_da = DocList[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(10)]
        )
        dep.index(inputs=index_da, request_size=1, return_type=DocList[TextDocWithId])
        responses = dep.search(inputs=index_da[0:1], request_size=1, return_type=DocList[ResultTestDoc])
        assert len(responses) == 1 if reduce else 2
        for r in responses:
            assert r.l[0] == 3
            assert len(r.matches) == 6
            for match in r.matches:
                assert 'ID' in match.text


@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http', 'websocket']])
@pytest.mark.parametrize('reduce', [True, False])
@pytest.mark.parametrize('sleep_time', [0.1, 5])
def test_flow_with_shards_all_shards_return(protocols, reduce, sleep_time):
    from docarray.documents import TextDoc
    from docarray import DocList, BaseDoc
    from typing import List

    class TextDocWithId(TextDoc):
        id: str
        l: List[int] = []

    class ResultTestDoc(BaseDoc):
        price: int = '2'
        l: List[int] = [3]
        matches: DocList[TextDocWithId]

    class SimilarityTestIndexer(Executor):
        """Simulates an indexer where no shard would fail, they all pass results"""

        def __init__(self, sleep_time=0.1, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._docs = DocList[TextDocWithId]()
            time.sleep(sleep_time)

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

    ports = [random_port() for _ in protocols]
    with Flow(protocol=protocols, port=ports).add(uses=SimilarityTestIndexer, uses_with={'sleep_time': sleep_time},
                                                  shards=2, reduce=reduce):
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            index_da = DocList[TextDocWithId](
                [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(10)]
            )
            c.index(inputs=index_da, request_size=1, return_type=DocList[TextDocWithId])
            responses = c.search(inputs=index_da[0:1], request_size=1, return_type=DocList[ResultTestDoc])
            assert len(responses) == 1 if reduce else 2
            for r in responses:
                assert r.l[0] == 3
                assert len(r.matches) == 6
                for match in r.matches:
                    assert 'ID' in match.text
