from typing import Optional, List, Dict, Union
import pytest
import time
import os
import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import ImageDoc
from docarray.typing import AnyTensor, ImageUrl
from docarray.documents import TextDoc
from docarray.documents.legacy import LegacyDocument
from jina.helper import random_port

from jina import Deployment, Executor, Flow, requests, Client
from jina.excepts import RuntimeFailToStart


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


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_condition_feature(protocol, temp_workspace, tmpdir):
    class ProcessingTestDocConditions(BaseDoc):
        text: str
        tags: Dict[str, int]

    class ConditionDumpExecutor(Executor):
        @requests
        def foo(self, docs: DocList[ProcessingTestDocConditions], **kwargs) -> DocList[ProcessingTestDocConditions]:
            with open(
                    os.path.join(str(self.workspace), f'{self.metas.name}.txt'), 'w', encoding='utf-8'
            ) as fp:
                for doc in docs:
                    fp.write(doc.text)
                    doc.text += f' processed by {self.metas.name}'


    class FirstExec(Executor):
        @requests
        def foo(self, docs: DocList[LegacyDocument], **kwargs) -> DocList[ProcessingTestDocConditions]:
            output_da = DocList[ProcessingTestDocConditions](
                [ProcessingTestDocConditions(text='type1', tags={'type': 1}),
                 ProcessingTestDocConditions(text='type2', tags={'type': 2})])
            return output_da

    class JoinerExec(Executor):
        @requests
        def foo(self, docs: DocList[ProcessingTestDocConditions], **kwargs) -> DocList[ProcessingTestDocConditions]:
            pass

    f = (
        Flow(protocol=protocol)
            .add(uses=FirstExec, name='first')
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
            .needs_all('joiner', uses=JoinerExec)
    )

    with f:
        input_da = DocList[LegacyDocument]([])

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


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_endpoints_target_executors_combinations(protocol):
    class Foo(Executor):
        @requests(on='/hello')
        def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
            for doc in docs:
                doc.text += 'Processed by foo'

    class Bar(Executor):
        @requests(on='/hello')
        def bar(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
            for doc in docs:
                doc.text += 'Processed by bar'

    f = Flow(protocol=protocol).add(name='p0', uses=Foo).add(name='p1', uses=Bar)

    with f:
        docs = f.post(
            '/hello',
            inputs=DocList[TextDoc]([TextDoc(text='')]),
            return_type=DocList[TextDoc]
        )
        assert len(docs) == 1
        for doc in docs:
            assert doc.text == 'Processed by fooProcessed by bar'
        docs = f.post(
            '/hello',
            target_executor='p1',
            inputs=DocList[TextDoc]([TextDoc(text='')]),
            return_type=DocList[TextDoc]
        )
        assert len(docs) == 1
        for doc in docs:
            assert doc.text == 'Processed by bar'


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_floating_executors(protocol, tmpdir):
    TIME_SLEEP_FLOATING = 1.0

    class FloatingTestExecutor(Executor):
        def __init__(self, file_name, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.file_name = file_name

        @requests
        def foo(self, docs: DocList[LegacyDocument], **kwargs) -> DocList[LegacyDocument]:
            time.sleep(TIME_SLEEP_FLOATING)
            with open(self.file_name, 'a+', encoding='utf-8') as f:
                f.write('here ')

            for d in docs:
                d.text = 'change it'

    NUM_REQ = 20
    file_name = os.path.join(str(tmpdir), 'file.txt')
    expected_str = 'here ' * NUM_REQ

    f = (
        Flow(protocol=protocol)
            .add(name='first')
            .add(
            name='second',
            floating=True,
            uses=FloatingTestExecutor,
            uses_with={'file_name': file_name},
        )
    )

    with f:
        for j in range(NUM_REQ):
            start_time = time.time()
            ret = f.post(on='/default', inputs=DocList[LegacyDocument]([LegacyDocument(text='')]))
            end_time = time.time()
            assert (
                           end_time - start_time
                   ) < TIME_SLEEP_FLOATING  # check that the response arrives before the
            # Floating Executor finishes
            assert len(ret) == 1
            assert ret[0].text == ''

    with open(file_name, 'r', encoding='utf-8') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
def test_empty_input_output(protocol, ctxt_manager):
    if ctxt_manager == 'deployment' and protocol == 'websocket':
        return

    class Foo(Executor):
        @requests(on='/hello')
        def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
            for doc in docs:
                doc.text += 'Processed by foo'

    if ctxt_manager == 'flow':
        ctxt_mgr = Flow(protocol=protocol).add(uses=Foo)
    else:
        ctxt_mgr = Deployment(protocol=protocol, uses=Foo)

    with ctxt_mgr:
        ret = ctxt_mgr.post(on='/hello', inputs=DocList[TextDoc]())
        assert len(ret) == 0


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
def test_send_parameters(protocol, ctxt_manager):
    if ctxt_manager == 'deployment' and protocol == 'websocket':
        return

    class Foo(Executor):
        @requests(on='/hello')
        def foo(self, docs: DocList[TextDoc], parameters, **kwargs) -> DocList[TextDoc]:
            for doc in docs:
                doc.text += f'Processed by foo with {parameters["param"]}'

    if ctxt_manager == 'flow':
        ctxt_mgr = Flow(protocol=protocol).add(uses=Foo)
    else:
        ctxt_mgr = Deployment(protocol=protocol, uses=Foo)

    with ctxt_mgr:
        ret = ctxt_mgr.post(on='/hello', parameters={'param': '5'}, inputs=DocList[TextDoc]([TextDoc(text='')]))
        assert len(ret) == 1
        assert ret[0].text == 'Processed by foo with 5'


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
def test_get_parameters_back(protocol, ctxt_manager):
    if ctxt_manager == 'deployment' and protocol == 'websocket':
        return

    class Foo(Executor):
        @requests(on='/hello')
        def foo(self, parameters, **kwargs):
            return {'back': parameters}

    if ctxt_manager == 'flow':
        ctxt_mgr = Flow(protocol=protocol).add(uses=Foo, name='foo')
    else:
        ctxt_mgr = Deployment(protocol=protocol, uses=Foo, name='foo')

    with ctxt_mgr:
        ret = ctxt_mgr.post(on='/hello', parameters={'param': '5'}, return_responses=True)
        assert len(ret) == 1
        assert ret[0].parameters == {'param': '5', '__results__': {'foo/rep-0': {'back': {'param': '5'}}}}


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
def test_raise_exception(protocol, ctxt_manager):
    from jina.excepts import BadServer
    if ctxt_manager == 'deployment' and protocol == 'websocket':
        return

    class Foo(Executor):
        @requests(on='/hello')
        def foo(self, **kwargs):
            raise Exception('Raising some exception from Executor')

    if ctxt_manager == 'flow':
        ctxt_mgr = Flow(protocol=protocol).add(uses=Foo, name='foo')
    else:
        ctxt_mgr = Deployment(protocol=protocol, uses=Foo, name='foo')

    with ctxt_mgr:
        if protocol == 'http':
            with pytest.raises(ValueError) as excinfo:
                ctxt_mgr.post(on='/hello', parameters={'param': '5'}, return_responses=True)
            assert excinfo.value.args[0] == {'detail': "Exception('Raising some exception from Executor')"}
        elif protocol == 'grpc':
            with pytest.raises(BadServer):
                ctxt_mgr.post(on='/hello', parameters={'param': '5'}, return_responses=True)
        elif protocol == 'websocket':
            with pytest.raises(BadServer):
                ctxt_mgr.post(on='/hello', parameters={'param': '5'}, return_responses=True)


def test_custom_gateway():
    from docarray import DocList
    from docarray.documents.text import TextDoc

    from jina.serve.runtimes.gateway.http import FastAPIBaseGateway
    from jina import Flow, Executor, requests

    PARAMETERS = {'dog': 'woof'}

    class MyGateway(FastAPIBaseGateway):
        @property
        def app(self):
            from fastapi import FastAPI

            app = FastAPI(title='Custom FastAPI Gateway')

            @app.get('/endpoint_executor')
            async def get_executor(text: str):
                docs = DocList[TextDoc]([TextDoc(text=f'executor {text}'), TextDoc(text=f'executor {text}'.upper())])
                resp = await self.executor['executor1'].post(on='/', inputs=docs, parameters=PARAMETERS,
                                                             return_type=DocList[TextDoc])
                return {'result': [doc.text for doc in resp]}

            @app.get('/endpoint_stream')
            async def get_endpoint_stream(text: str):
                docs = DocList[TextDoc]([TextDoc(text=f'stream {text}'), TextDoc(text=f'stream {text}'.upper())])
                async for resp in self.streamer.stream_docs(docs, parameters=PARAMETERS, target_executor='executor1'):
                    return {'result': [doc.text for doc in resp]}

            return app

    class FirstExec(Executor):
        @requests
        def func(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
            for doc in docs:
                doc.text += ' THIS SHOULD NOT HAVE HAPPENED!'

    class SecondExec(Executor):
        @requests
        def func(self, docs: DocList[TextDoc], parameters, **kwargs) -> DocList[TextDoc]:
            for doc in docs:
                doc.text += f' Second(parameters={str(parameters)})'

    with Flow().config_gateway(uses=MyGateway, protocol='http').add(uses=FirstExec, name='executor0').add(
            uses=SecondExec, name='executor1') as flow:
        import requests
        r = requests.get(f'http://localhost:{flow.port}/endpoint_executor?text=meow')
        assert r.json()['result'] == [f'executor meow Second(parameters={str(PARAMETERS)})',
                                      f'EXECUTOR MEOW Second(parameters={str(PARAMETERS)})']

        r = requests.get(f'http://localhost:{flow.port}/endpoint_stream?text=meow')
        assert r.json()['result'] == [f'stream meow Second(parameters={str(PARAMETERS)})',
                                      f'STREAM MEOW Second(parameters={str(PARAMETERS)})']


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
def test_any_endpoint(protocol, ctxt_manager):
    if ctxt_manager == 'deployment' and protocol == 'websocket':
        return

    class Foo(Executor):
        @requests
        def foo(self, docs: DocList[TextDoc], parameters, **kwargs) -> DocList[TextDoc]:
            for doc in docs:
                doc.text = 'Foo'

    if ctxt_manager == 'flow':
        ctxt_mgr = Flow(protocol=protocol).add(uses=Foo, name='foo')
    else:
        ctxt_mgr = Deployment(protocol=protocol, uses=Foo, name='foo')

    with ctxt_mgr:
        ret = ctxt_mgr.post(on='/index', inputs=DocList[TextDoc]([TextDoc(text='')]))
        assert len(ret) == 1
        assert ret[0].text == 'Foo'


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_flow_incompatible_linear(protocol):
    class First(Executor):
        @requests
        def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
            pass

    class Second(Executor):
        @requests
        def foo(self, docs: DocList[ImageDoc], **kwargs) -> DocList[ImageDoc]:
            pass

    f = Flow(protocol=protocol).add(uses=First).add(uses=Second)

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_flow_incompatible_bifurcation(protocol):
    class First(Executor):
        @requests
        def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
            pass

    class Second(Executor):
        @requests
        def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[ImageDoc]:
            pass

    class Previous(Executor):
        @requests
        def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
            pass

    f = Flow(protocol=protocol).add(uses=Previous, name='previous').add(uses=First, name='first', needs='previous').add(uses=Second, name='second', needs='previous').needs_all()

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass



class ExternalDeploymentDoc(BaseDoc):
    tags: Dict[str, str] = {}


@pytest.fixture(scope='function')
def input_docs():
    return DocList[ExternalDeploymentDoc]([ExternalDeploymentDoc() for _ in range(50)])


@pytest.fixture
def num_shards(request):
    return request.param


def _external_deployment_args(num_shards, port=None):
    from jina.parsers import set_deployment_parser

    args = [
        '--uses',
        'MyExternalExecutor',
        '--name',
        'external_real',
        '--port',
        str(port) if port else str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


@pytest.fixture(scope='function')
def external_deployment_args(num_shards, port=None):
    return _external_deployment_args(num_shards, port)


@pytest.fixture
def external_deployment(external_deployment_args):
    return Deployment(external_deployment_args)


import uuid


class MyExternalExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = str(uuid.uuid4())

    @requests(on='/index')
    def foo(self, docs, *args, **kwargs):
        for doc in docs:
            doc.tags['name'] = self.runtime_args.name
            doc.tags['uuid'] = self._id


@pytest.mark.parametrize('num_shards', [1, 2], indirect=True)
@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_flow_with_external_deployment(
        external_deployment, external_deployment_args, input_docs, num_shards, protocol
):
    with external_deployment:
        external_args = vars(external_deployment_args)
        del external_args['name']
        del external_args['external']
        del external_args['deployment_role']
        flow = Flow(protocol=protocol).add(
            **external_args,
            name='external_fake',
            external=True,
        )
        with flow:
            resp = flow.index(inputs=input_docs)

        assert len(resp) == len(input_docs)
        assert len(resp) > 0
        for doc in resp:
            assert 'external_real' in doc.tags['name']


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
