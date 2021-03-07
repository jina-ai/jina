import os

import numpy as np
import pytest

from jina import Flow, Document
from jina.enums import SocketType, FlowBuildLevel
from jina.excepts import RuntimeFailToStart
from jina.executors import BaseExecutor
from jina.helper import random_identity
from jina.proto.jina_pb2 import DocumentProto
from jina.types.request import Response
from jina.peapods.pods import BasePod
from tests import random_docs, validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_flow_with_jump(tmpdir):
    def _validate(f):
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND
        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r4']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r5']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r6']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r8']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r9']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT
        node = f._pod_nodes['r10']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_BIND
        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args

    f = (
        Flow()
        .add(name='r1')
        .add(name='r2')
        .add(name='r3', needs='r1')
        .add(name='r4', needs='r2')
        .add(name='r5', needs='r3')
        .add(name='r6', needs='r4')
        .add(name='r8', needs='r6')
        .add(name='r9', needs='r5')
        .add(name='r10', needs=['r9', 'r8'])
    )

    with f:
        _validate(f)

    f.save_config(os.path.join(str(tmpdir), 'tmp.yml'))
    Flow.load_config(os.path.join(str(tmpdir), 'tmp.yml'))

    with Flow.load_config(os.path.join(str(tmpdir), 'tmp.yml')) as f:
        _validate(f)


@pytest.mark.parametrize('restful', [False, True])
def test_simple_flow(restful):
    bytes_gen = (Document() for _ in range(10))

    def bytes_fn():
        for _ in range(100):
            yield Document()

    f = Flow(restful=restful).add()

    with f:
        f.index(inputs=bytes_gen)

    with f:
        f.index(inputs=bytes_fn)

    with f:
        f.index(inputs=bytes_fn)
        f.index(inputs=bytes_fn)

        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

    assert 'gateway' not in f

    node = f._pod_nodes['pod0']
    assert node.head_args.socket_in == SocketType.PULL_BIND
    assert node.tail_args.socket_out == SocketType.PUSH_BIND

    for name, node in f._pod_nodes.items():
        assert node.peas_args['peas'][0] == node.head_args
        assert node.peas_args['peas'][0] == node.tail_args


def test_flow_identical(tmpdir):
    with open(os.path.join(cur_dir, '../yaml/test-flow.yml')) as fp:
        a = Flow.load_config(fp)

    b = (
        Flow()
        .add(name='chunk_seg', parallel=3)
        .add(name='wqncode1', parallel=2)
        .add(name='encode2', parallel=2, needs='chunk_seg')
        .join(['wqncode1', 'encode2'])
    )

    a.save_config(os.path.join(str(tmpdir), 'test2.yml'))

    c = Flow.load_config(os.path.join(str(tmpdir), 'test2.yml'))

    assert a == b
    assert a == c

    with a as f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['chunk_seg']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['wqncode1']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['encode2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT


@pytest.mark.parametrize('restful', [False, True])
def test_flow_no_container(restful):
    f = Flow(restful=restful).add(
        name='dummyEncoder',
        uses=os.path.join(cur_dir, '../mwu-encoder/mwu_encoder.yml'),
    )

    with f:
        f.index(inputs=random_docs(10))


@pytest.fixture
def docpb_workspace(tmpdir):
    os.environ['TEST_DOCSHARD_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['TEST_DOCSHARD_WORKSPACE']


def test_shards(docpb_workspace):
    f = Flow().add(
        name='doc_pb', uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'), parallel=3
    )
    with f:
        f.index(inputs=random_docs(1000), random_doc_id=False)
    with f:
        pass


def test_py_client():
    f = (
        Flow()
        .add(name='r1')
        .add(name='r2')
        .add(name='r3', needs='r1')
        .add(name='r4', needs='r2')
        .add(name='r5', needs='r3')
        .add(name='r6', needs='r4')
        .add(name='r8', needs='r6')
        .add(name='r9', needs='r5')
        .add(name='r10', needs=['r9', 'r8'])
    )

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r4']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r5']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r6']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r8']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r9']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r10']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_BIND

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_dry_run_with_two_pathways_diverging_at_gateway():
    f = Flow().add(name='r2').add(name='r3', needs='gateway').join(['r2', 'r3'])

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_dry_run_with_two_pathways_diverging_at_non_gateway():
    f = (
        Flow()
        .add(name='r1')
        .add(name='r2')
        .add(name='r3', needs='r1')
        .join(['r2', 'r3'])
    )

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_refactor_num_part():
    f = (
        Flow()
        .add(name='r1', uses='_logforward', needs='gateway')
        .add(name='r2', uses='_logforward', needs='gateway')
        .join(['r1', 'r2'])
    )

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_refactor_num_part_proxy():
    f = (
        Flow()
        .add(name='r1', uses='_logforward')
        .add(name='r2', uses='_logforward', needs='r1')
        .add(name='r3', uses='_logforward', needs='r1')
        .join(['r2', 'r3'])
    )

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


@pytest.mark.parametrize('restful', [False, True])
def test_refactor_num_part_proxy_2(restful):
    f = (
        Flow(restful=restful)
        .add(name='r1', uses='_logforward')
        .add(name='r2', uses='_logforward', needs='r1', parallel=2)
        .add(name='r3', uses='_logforward', needs='r1', parallel=3, polling='ALL')
        .needs(['r2', 'r3'])
    )

    with f:
        f.index(['abbcs', 'efgh'])


@pytest.mark.parametrize('restful', [False, True])
def test_refactor_num_part_2(restful):
    f = Flow(restful=restful).add(
        name='r1', uses='_logforward', needs='gateway', parallel=3, polling='ALL'
    )

    with f:
        f.index(['abbcs', 'efgh'])

    f = Flow(restful=restful).add(
        name='r1', uses='_logforward', needs='gateway', parallel=3
    )

    with f:
        f.index(['abbcs', 'efgh'])


@pytest.fixture()
def datauri_workspace(tmpdir):
    os.environ['TEST_DATAURIINDEX_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['TEST_DATAURIINDEX_WORKSPACE']


@pytest.mark.parametrize('restful', [False, True])
def test_index_text_files(mocker, restful, datauri_workspace):
    def validate(req):
        assert len(req.docs) > 0
        for d in req.docs:
            assert d.text

    response_mock = mocker.Mock()

    f = Flow(restful=restful, read_only=True).add(
        uses=os.path.join(cur_dir, '../yaml/datauriindex.yml'), timeout_ready=-1
    )

    with f:
        f.index_files('*.py', on_done=response_mock)

    validate_callback(response_mock, validate)


# TODO(Deepankar): Gets stuck when `restful: True` - issues with `needs='gateway'`
@pytest.mark.parametrize('restful', [False])
def test_flow_with_publish_driver(mocker, restful):
    def validate(req):
        for d in req.docs:
            assert d.embedding is not None

    response_mock = mocker.Mock()

    f = (
        Flow(restful=restful)
        .add(name='r2', uses='!OneHotTextEncoder')
        .add(name='r3', uses='!OneHotTextEncoder', needs='gateway')
        .join(needs=['r2', 'r3'])
    )

    with f:
        f.index(['text_1', 'text_2'], on_done=response_mock)

    validate_callback(response_mock, validate)


@pytest.mark.parametrize('restful', [False, True])
def test_flow_with_modalitys_simple(mocker, restful):
    def validate(req):
        for d in req.index.docs:
            assert d.modality in ['mode1', 'mode2']

    def input_function():
        doc1 = DocumentProto()
        doc1.modality = 'mode1'
        doc2 = DocumentProto()
        doc2.modality = 'mode2'
        doc3 = DocumentProto()
        doc3.modality = 'mode1'
        return [doc1, doc2, doc3]

    response_mock = mocker.Mock()

    flow = (
        Flow(restful=restful)
        .add(name='chunk_seg', parallel=3)
        .add(
            name='encoder12',
            parallel=2,
            uses='- !FilterQL | {lookups: {modality__in: [mode1, mode2]}, traversal_paths: [c]}',
        )
    )
    with flow:
        flow.index(inputs=input_function, on_done=response_mock)

    validate_callback(response_mock, validate)


def test_flow_arguments_priorities():
    f = Flow(port_expose=12345).add(name='test', port_expose=23456)
    assert f._pod_nodes['test'].args.port_expose == 23456

    f = Flow(port_expose=12345).add(name='test')
    assert f._pod_nodes['test'].args.port_expose == 12345


@pytest.mark.parametrize('restful', [False])
def test_flow_arbitrary_needs(restful):
    f = (
        Flow(restful=restful)
        .add(name='p1')
        .add(name='p2', needs='gateway')
        .add(name='p3', needs='gateway')
        .add(name='p4', needs='gateway')
        .add(name='p5', needs='gateway')
        .needs(['p2', 'p4'], name='r1')
        .needs(['p3', 'p5'], name='r2')
        .needs(['p1', 'r1'], name='r3')
        .needs(['r2', 'r3'], name='r4')
    )

    with f:
        f.index(['abc', 'def'])


@pytest.mark.parametrize('restful', [False])
def test_flow_needs_all(restful):
    f = Flow(restful=restful).add(name='p1', needs='gateway').needs_all(name='r1')
    assert f._pod_nodes['r1'].needs == {'p1'}

    f = (
        Flow(restful=restful)
        .add(name='p1', needs='gateway')
        .add(name='p2', needs='gateway')
        .add(name='p3', needs='gateway')
        .needs(needs=['p1', 'p2'], name='r1')
        .needs_all(name='r2')
    )
    assert f._pod_nodes['r2'].needs == {'p3', 'r1'}

    with f:
        f.index_ndarray(np.random.random([10, 10]))

    f = (
        Flow(restful=restful)
        .add(name='p1', needs='gateway')
        .add(name='p2', needs='gateway')
        .add(name='p3', needs='gateway')
        .needs(needs=['p1', 'p2'], name='r1')
        .needs_all(name='r2')
        .add(name='p4', needs='r2')
    )
    assert f._pod_nodes['r2'].needs == {'p3', 'r1'}
    assert f._pod_nodes['p4'].needs == {'r2'}

    with f:
        f.index_ndarray(np.random.random([10, 10]))


def test_flow_with_pod_envs():
    f = Flow.load_config('yaml/flow-with-envs.yml')

    class EnvChecker1(BaseExecutor):
        """Class used in Flow YAML"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # pea/pod-specific
            assert os.environ['key1'] == 'value1'
            assert os.environ['key2'] == 'value2'
            # inherit from parent process
            assert os.environ['key_parent'] == 'value3'

    class EnvChecker2(BaseExecutor):
        """Class used in Flow YAML"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # pea/pod-specific
            assert 'key1' not in os.environ
            assert 'key2' not in os.environ
            # inherit from parent process
            assert os.environ['key_parent'] == 'value3'

    with f:
        pass


@pytest.mark.parametrize('return_results', [False, True])
@pytest.mark.parametrize('restful', [False, True])
def test_return_results_sync_flow(return_results, restful):
    with Flow(restful=restful, return_results=return_results).add() as f:
        r = f.index_ndarray(np.random.random([10, 2]))
        if return_results:
            assert isinstance(r, list)
            assert isinstance(r[0], Response)
        else:
            assert r is None


@pytest.mark.parametrize(
    'input, expect_host, expect_port',
    [
        ('0.0.0.0', '0.0.0.0', None),
        ('0.0.0.0:12345', '0.0.0.0', 12345),
        ('123.456.789.0:45678', '123.456.789.0', 45678),
        ('api.jina.ai:45678', 'api.jina.ai', 45678),
    ],
)
def test_flow_host_expose_shortcut(input, expect_host, expect_port):
    f = Flow().add(host=input).build()
    assert f['pod0'].args.host == expect_host
    if expect_port is not None:
        assert f['pod0'].args.port_expose == expect_port


def test_flow_workspace_id():
    f = Flow().add().add().add().build()
    assert len(f.workspace_id) == 3
    assert len(set(f.workspace_id.values())) == 3

    with pytest.raises(ValueError):
        f.workspace_id = 'hello'

    new_id = random_identity()
    f.workspace_id = new_id
    assert len(set(f.workspace_id.values())) == 1
    assert list(f.workspace_id.values())[0] == new_id


def test_flow_identity():
    f = Flow().add().add().add().build()
    assert len(f.identity) == 4
    assert len(set(f.identity.values())) == 4

    with pytest.raises(ValueError):
        f.identity = 'hello'

    new_id = random_identity()
    f.identity = new_id
    assert len(set(f.identity.values())) == 1
    assert list(f.identity.values())[0] == new_id
    assert f.args.identity == new_id


def test_flow_identity_override():
    f = Flow().add().add(parallel=2).add(parallel=2)

    with f:
        assert len(set(p.args.identity for _, p in f)) == f.num_pods

    f = Flow(identity='123456').add().add(parallel=2).add(parallel=2)

    with f:
        assert len(set(p.args.identity for _, p in f)) == 1

    y = '''
!Flow
version: '1.0'
pods:
    - uses: _pass
    - uses: _pass
      parallel: 3
    '''

    f = Flow.load_config(y)
    for _, p in f:
        p.args.identity = '1234'

    with f:
        assert len(set(p.args.identity for _, p in f)) == 2
        for _, p in f:
            if p.args.identity != '1234':
                assert p.name == 'gateway'


def test_bad_pod_graceful_termination():
    def asset_bad_flow(f):
        with pytest.raises(RuntimeFailToStart):
            with f:
                assert f._build_level == FlowBuildLevel.EMPTY

    # bad remote pod
    asset_bad_flow(Flow().add(host='hello-there'))

    # bad local pod
    asset_bad_flow(Flow().add(uses='hello-there'))

    # bad local pod at second
    asset_bad_flow(Flow().add().add(uses='hello-there'))

    # bad remote pod at second
    asset_bad_flow(Flow().add().add(host='hello-there'))

    # bad local pod at second, with correct pod at last
    asset_bad_flow(Flow().add().add(uses='hello-there').add())

    # bad remote pod at second, with correct pod at last
    asset_bad_flow(Flow().add().add(host='hello-there').add())


def test_socket_types_2_remote_one_local():
    f = (
        Flow()
        .add(name='pod1', host='0.0.0.1')
        .add(name='pod2', parallel=2, host='0.0.0.2')
        .add(name='pod3', parallel=2, host='1.2.3.4', needs=['gateway'])
        .join(name='join', needs=['pod2', 'pod3'])
    )

    f.build()

    assert f._pod_nodes['join'].head_args.socket_in == SocketType.PULL_BIND
    assert f._pod_nodes['pod2'].tail_args.socket_out == SocketType.PUSH_CONNECT
    assert f._pod_nodes['pod3'].tail_args.socket_out == SocketType.PUSH_CONNECT


def test_socket_types_2_remote_one_local_input_socket_pull_connect_from_remote():
    f = (
        Flow()
        .add(name='pod1', host='0.0.0.1')
        .add(name='pod2', parallel=2, host='0.0.0.2')
        .add(name='pod3', parallel=2, host='1.2.3.4', needs=['gateway'])
        .join(name='join', needs=['pod2', 'pod3'])
    )

    f.build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f._pod_nodes['join'].head_args.socket_in == SocketType.PULL_BIND
    assert f._pod_nodes['pod2'].tail_args.socket_out == SocketType.PUSH_CONNECT
    assert f._pod_nodes['pod3'].tail_args.socket_out == SocketType.PUSH_CONNECT


def test_single_document_flow_index():
    d = Document()
    with Flow().add() as f:
        f.index(d)
        f.index(lambda: d)


def test_flow_equalities():
    f1 = Flow().add().add(needs='gateway').needs_all(name='joiner')
    f2 = (
        Flow()
        .add(name='pod0')
        .add(name='pod1', needs='gateway')
        .add(name='joiner', needs=['pod0', 'pod1'])
    )
    assert f1 == f2

    f2 = f2.add()
    assert f1 != f2


def test_flow_get_item():
    f1 = Flow().add().add(needs='gateway').needs_all(name='joiner')
    assert isinstance(f1[1], BasePod)
    assert isinstance(f1['pod0'], BasePod)


def test_flow_yaml_dump():
    import io

    f = io.StringIO()
    f1 = Flow().add()
    with f1:
        f1.to_swarm_yaml(path=f)
        assert 'gateway' in f.getvalue()
        assert 'services' in f.getvalue()
        assert 'jina pod' in f.getvalue()

    assert '!Flow' in f1.yaml_spec
