import datetime
import inspect
import json
import os

import numpy as np
import pytest

from jina import Flow, Document, Executor, requests, __windows__
from jina.enums import InfrastructureType, SocketType, FlowBuildLevel, PollingType
from jina.excepts import RuntimeFailToStart
from jina.executors import BaseExecutor
from jina.helper import random_identity
from jina.peapods.pods import BasePod
from jina.types.document.generators import from_ndarray
from jina.types.request import Response
from jina.proto import jina_pb2
from tests import random_docs, validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.slow
def test_flow_with_jump(tmpdir):
    def _validate(f):
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r4']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r5']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r6']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r8']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r9']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
        node = f._pod_nodes['r10']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND
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


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_simple_flow(protocol):
    bytes_gen = (Document() for _ in range(10))

    def bytes_fn():
        for _ in range(100):
            yield Document()

    f = Flow(protocol=protocol).add(name='executor0')

    with f:
        f.index(inputs=bytes_gen)

    with f:
        f.index(inputs=bytes_fn)

    with f:
        f.index(inputs=bytes_fn)
        f.index(inputs=bytes_fn)

        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

    assert 'gateway' not in f

    node = f._pod_nodes['executor0']
    assert node.head_args.socket_in == SocketType.ROUTER_BIND
    assert node.tail_args.socket_out == SocketType.ROUTER_BIND

    for name, node in f._pod_nodes.items():
        assert node.peas_args['peas'][0] == node.head_args
        assert node.peas_args['peas'][0] == node.tail_args


@pytest.mark.slow
def test_flow_identical(tmpdir):
    with open(os.path.join(cur_dir, '../yaml/test-flow.yml')) as fp:
        a = Flow.load_config(fp)

    b = (
        Flow()
        .add(name='chunk_seg', shards=3)
        .add(name='wqncode1', shards=2)
        .add(name='encode2', shards=2, needs='chunk_seg')
        .join(['wqncode1', 'encode2'])
    )

    a.save_config(os.path.join(str(tmpdir), 'test2.yml'))

    c = Flow.load_config(os.path.join(str(tmpdir), 'test2.yml'))

    assert a == b
    assert a == c

    with a as f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['chunk_seg']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.shards_args:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['wqncode1']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.shards_args:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['encode2']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.shards_args:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_no_container(protocol):
    f = Flow(protocol=protocol).add(
        name='dummyEncoder',
        uses=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder.yml'),
    )

    with f:
        f.index(inputs=random_docs(10))


@pytest.fixture
def docpb_workspace(tmpdir):
    os.environ['TEST_DOCSHARD_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['TEST_DOCSHARD_WORKSPACE']


@pytest.mark.slow
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
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r4']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r5']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r6']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r8']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r9']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r10']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_dry_run_with_two_pathways_diverging_at_gateway():
    f = Flow().add(name='r2').add(name='r3', needs='gateway').join(['r2', 'r3'])

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

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
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_refactor_num_part():
    f = (
        Flow()
        .add(name='r1', needs='gateway')
        .add(name='r2', needs='gateway')
        .join(['r1', 'r2'])
    )

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


def test_refactor_num_part_proxy():
    f = (
        Flow()
        .add(name='r1')
        .add(name='r2', needs='r1')
        .add(name='r3', needs='r1')
        .join(['r2', 'r3'])
    )

    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r1']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r2']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        node = f._pod_nodes['r3']
        assert node.head_args.socket_in == SocketType.ROUTER_BIND
        assert node.tail_args.socket_out == SocketType.ROUTER_BIND

        for name, node in f._pod_nodes.items():
            assert node.peas_args['peas'][0] == node.head_args
            assert node.peas_args['peas'][0] == node.tail_args


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_refactor_num_part_proxy_2(protocol):
    f = (
        Flow(protocol=protocol)
        .add(name='r1')
        .add(name='r2', needs='r1', shards=2)
        .add(name='r3', needs='r1', shards=3, polling='ALL')
        .needs(['r2', 'r3'])
    )

    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')])


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_refactor_num_part_2(protocol):
    f = Flow(protocol=protocol).add(name='r1', needs='gateway', shards=3, polling='ALL')

    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')])

    f = Flow(protocol=protocol).add(name='r1', needs='gateway', shards=3)

    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')])


@pytest.fixture()
def datauri_workspace(tmpdir):
    os.environ['TEST_DATAURIINDEX_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['TEST_DATAURIINDEX_WORKSPACE']


class DummyOneHotTextEncoder(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            d.embedding = np.array([1, 2, 3])


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_with_publish_driver(protocol):
    def validate(req):
        for d in req.docs:
            assert d.embedding is not None

    f = (
        Flow(protocol=protocol)
        .add(name='r2', uses=DummyOneHotTextEncoder)
        .add(name='r3', uses=DummyOneHotTextEncoder, needs='gateway')
        .join(needs=['r2', 'r3'])
    )

    with f:
        results = f.index(
            [Document(text='text_1'), Document(text='text_2')], return_results=True
        )

    validate(results[0])


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_arbitrary_needs(protocol):
    f = (
        Flow(protocol=protocol)
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
        f.index([Document(text='abbcs'), Document(text='efgh')])


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_needs_all(protocol):
    f = Flow(protocol=protocol).add(name='p1', needs='gateway').needs_all(name='r1')
    assert f._pod_nodes['r1'].needs == {'p1'}

    f = (
        Flow(protocol=protocol)
        .add(name='p1', needs='gateway')
        .add(name='p2', needs='gateway')
        .add(name='p3', needs='gateway')
        .needs(needs=['p1', 'p2'], name='r1')
        .needs_all(name='r2')
    )
    assert f._pod_nodes['r2'].needs == {'p3', 'r1'}

    with f:
        f.index(from_ndarray(np.random.random([10, 10])))

    f = (
        Flow(protocol=protocol)
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
        f.index(from_ndarray(np.random.random([10, 10])))


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


def test_flow_with_pod_envs():
    f = Flow.load_config(os.path.join(cur_dir, 'yaml/flow-with-envs.yml'))
    with f:
        pass


@pytest.mark.slow
@pytest.mark.parametrize('return_results', [False, True])
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_return_results_sync_flow(return_results, protocol):
    with Flow(protocol=protocol).add() as f:
        r = f.index(
            from_ndarray(np.random.random([10, 2])), return_results=return_results
        )
        if return_results:
            assert isinstance(r, list)
            assert isinstance(r[0], Response)
            assert len(r[0].docs) == 10
            for doc in r[0].docs:
                assert isinstance(doc, Document)

            assert len(r[0].data.docs) == 10
            for doc in r[0].data.docs:
                assert isinstance(doc, jina_pb2.DocumentProto)

        else:
            assert r is None


@pytest.mark.parametrize(
    'input, expect_host, expect_port',
    [
        ('0.0.0.0', '0.0.0.0', None),
        ('0.0.0.0:12345', '0.0.0.0', 12345),
        ('123.124.125.0:45678', '123.124.125.0', 45678),
        ('api.jina.ai:45678', 'api.jina.ai', 45678),
    ],
)
def test_flow_host_expose_shortcut(input, expect_host, expect_port):
    f = Flow().add(host=input).build()
    assert f['executor0'].args.host == expect_host
    if expect_port is not None:
        assert f['executor0'].args.port_jinad == expect_port


def test_flow_workspace_id():
    f = Flow().add().add().add().build()
    assert len(f.workspace_id) == 4
    assert len(set(f.workspace_id.values())) == 4

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


@pytest.mark.slow
def test_flow_identity_override():
    f = Flow().add().add(shards=2).add(shards=2)

    with f:
        assert len(set(p.args.identity for _, p in f)) == f.num_pods

    f = Flow(identity='123456').add().add(shards=2).add(shards=2)

    with f:
        assert len(set(p.args.identity for _, p in f)) == 1

    y = '''
!Flow
version: '1.0'
executors:
    - name: hello
    - name: world
      shards: 3
    '''

    f = Flow.load_config(y)
    for _, p in f:
        p.args.identity = '1234'

    with f:
        assert len(set(p.args.identity for _, p in f)) == 2
        for _, p in f:
            if p.args.identity != '1234':
                assert p.name == 'gateway'


@pytest.mark.slow
def test_bad_pod_graceful_termination():
    def asset_bad_flow(f):
        with pytest.raises(RuntimeFailToStart):
            with f:
                assert f._build_level == FlowBuildLevel.EMPTY

    # bad remote pod
    asset_bad_flow(Flow().add(name='exec1', host='hello-there'))

    # bad local pod
    asset_bad_flow(Flow().add(name='exec2', uses='hello-there'))

    # bad local pod at second
    asset_bad_flow(Flow().add().add(name='exec3', uses='hello-there'))

    # bad remote pod at second
    asset_bad_flow(Flow().add().add(name='exec4', host='hello-there'))

    # bad local pod at second, with correct pod at last
    asset_bad_flow(Flow().add().add(name='exec5', uses='hello-there').add())

    # bad remote pod at second, with correct pod at last
    asset_bad_flow(Flow().add().add(name='exec6', host='hello-there').add())


def test_socket_types_2_remote_one_local():
    f = (
        Flow()
        .add(name='executor1', host='0.0.0.1')
        .add(name='executor2', shards=2, host='0.0.0.2')
        .add(name='executor3', shards=2, host='1.2.3.4', needs=['gateway'])
        .join(name='join', needs=['executor2', 'executor3'])
    )

    f.build()

    assert f._pod_nodes['join'].head_args.socket_in == SocketType.ROUTER_BIND
    assert f._pod_nodes['executor2'].tail_args.socket_out == SocketType.ROUTER_BIND
    assert f._pod_nodes['executor3'].tail_args.socket_out == SocketType.ROUTER_BIND


def test_socket_types_2_remote_one_local_input_socket_pull_connect_from_remote():
    f = (
        Flow()
        .add(name='executor1', host='0.0.0.1')
        .add(name='executor2', shards=2, host='0.0.0.2')
        .add(name='executor3', shards=2, host='1.2.3.4', needs=['gateway'])
        .join(name='join', needs=['executor2', 'executor3'])
    )

    f.build()

    assert f._pod_nodes['join'].head_args.socket_in == SocketType.ROUTER_BIND
    assert f._pod_nodes['executor2'].tail_args.socket_out == SocketType.ROUTER_BIND
    assert f._pod_nodes['executor3'].tail_args.socket_out == SocketType.ROUTER_BIND


def test_single_document_flow_index():
    d = Document()
    with Flow().add() as f:
        f.index(d)
        f.index(lambda: d)


def test_flow_equalities():
    f1 = (
        Flow()
        .add(name='executor0')
        .add(name='executor1', needs='gateway')
        .needs_all(name='joiner')
    )
    f2 = (
        Flow()
        .add(name='executor0')
        .add(name='executor1', needs='gateway')
        .add(name='joiner', needs=['executor0', 'executor1'])
    )
    assert f1 == f2

    f2 = f2.add(name='executor0')
    assert f1 != f2


def test_flow_get_item():
    f1 = Flow().add().add(needs='gateway').needs_all(name='joiner')
    assert isinstance(f1[1], BasePod)
    assert isinstance(f1['executor0'], BasePod)


class CustomizedExecutor(BaseExecutor):
    pass


def test_flow_add_class():
    f = Flow().add(uses=BaseExecutor).add(uses=CustomizedExecutor)

    with f:
        pass


@pytest.mark.slow
def test_flow_allinone_yaml():
    f = Flow.load_config(os.path.join(cur_dir, 'yaml/flow-allinone.yml'))
    with f:
        pass

    f = Flow.load_config(os.path.join(cur_dir, 'yaml/flow-allinone-oldstyle.yml'))
    with f:
        pass


class MyExec(Executor):
    @requests
    def foo(self, parameters, **kwargs):
        assert parameters['hello'] == 'world'


def test_flow_empty_data_request(mocker):
    f = Flow().add(uses=MyExec)

    mock = mocker.Mock()

    with f:
        f.post('/hello', parameters={'hello': 'world'}, on_done=mock)

    mock.assert_called()


def test_flow_common_kwargs():

    with Flow(name='hello', something_random=True).add() as f:
        assert f._common_kwargs == {'something_random': True}


@pytest.mark.parametrize('is_async', [True, False])
def test_flow_set_asyncio_switch_post(is_async):
    f = Flow(asyncio=is_async)
    assert inspect.isasyncgenfunction(f.post) == is_async


async def delayed_send_message_via(self, socket, msg):
    try:
        if self.msg_sent > 0:
            import asyncio

            await asyncio.sleep(1)
        from jina.peapods.zmq import send_message_async

        num_bytes = await send_message_async(socket, msg, **self.send_recv_kwargs)
        self.bytes_sent += num_bytes
        self.msg_sent += 1
    except (asyncio.CancelledError, TypeError) as ex:
        self.logger.error(f'sending message error: {ex!r}, gateway cancelled?')


@pytest.mark.skipif(__windows__, reason='timing comparison is broken for 2nd Flow')
def test_flow_routes_list(monkeypatch):
    def _time(time: str):
        return datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ')

    with Flow().add(name='executor1') as simple_flow:

        def validate_routes(x):
            gateway_entry, pod1_entry = json.loads(x.json())['routes']
            assert gateway_entry['pod'] == 'gateway'
            assert pod1_entry['pod'].startswith('executor1')
            assert (
                _time(gateway_entry['end_time'])
                > _time(pod1_entry['end_time'])
                > _time(pod1_entry['start_time'])
                > _time(gateway_entry['start_time'])
            )

        simple_flow.index(inputs=Document(), on_done=validate_routes)

    from jina.peapods.zmq import AsyncZmqlet

    # we are adding an artificial delay after message is sent to a1, so that the a branch completed before b1 starts
    monkeypatch.setattr(AsyncZmqlet, '_send_message_via', delayed_send_message_via)

    with Flow().add(name='a1').add(name='a2').add(name='b1', needs='gateway').add(
        name='merge', needs=['a2', 'b1']
    ) as shards_flow:

        def validate_routes(x):
            gateway_entry, a1_entry, a2_entry, b1_entry, merge_entry = json.loads(
                x.json()
            )['routes']
            assert gateway_entry['pod'] == 'gateway'
            assert a1_entry['pod'].startswith('a1')
            assert a2_entry['pod'].startswith('a2')
            assert b1_entry['pod'].startswith('b1')
            assert merge_entry['pod'].startswith('merge')
            assert (
                _time(gateway_entry['end_time'])
                > _time(merge_entry['end_time'])
                > _time(merge_entry['start_time'])
                > _time(b1_entry['end_time'])
                > _time(b1_entry['start_time'])
                > _time(a2_entry['end_time'])
                > _time(a2_entry['start_time'])
                > _time(a1_entry['end_time'])
                > _time(a1_entry['start_time'])
                > _time(gateway_entry['start_time'])
            )

        shards_flow.index(inputs=Document(), on_done=validate_routes)


def test_connect_to_predecessor():
    f = Flow().add(name='executor1').add(name='executor2', connect_to_predecessor=True)

    f.build()

    assert len(f._pod_nodes['gateway'].head_args.hosts_in_connect) == 0
    assert len(f._pod_nodes['executor1'].head_args.hosts_in_connect) == 0
    assert len(f._pod_nodes['executor2'].head_args.hosts_in_connect) == 1


def test_flow_grpc_with_shard():
    with pytest.raises(
        NotImplementedError, match='GRPC data runtime does not support sharding'
    ):
        Flow(grpc_data_requests=True).add(shards=2)
        Flow(grpc_data_requests=True).add(shards=None)

    Flow(grpc_data_requests=False).add(shards=1)
    Flow(grpc_data_requests=False).add()
    Flow(grpc_data_requests=True, infrastructure=InfrastructureType.K8S).add(shards=2)


def test_flow_auto_polling():
    f = (
        Flow()
        .add(name='pod_replica_only_polling_any', replicas=2)
        .add(name='pod_replica_only_polling_ignored', replicas=2, polling='ALL')
        .add(name='pod_replicas_shards_auto_polling_all', replicas=2, shards=2)
        .add(name='pod_shards_default_polling_any', shards=2)
        .add(
            name='pod_replicas_shards_manual_polling_any',
            replicas=2,
            shards=2,
            polling='ANY',
        )
        .add(
            name='pod_replicas_shards_manual_polling_all',
            replicas=2,
            shards=2,
            polling='ALL',
        )
    )

    assert f['pod_replica_only_polling_any'].args.polling == PollingType.ANY
    assert f['pod_replica_only_polling_ignored'].args.polling == PollingType.ANY
    assert f['pod_replicas_shards_auto_polling_all'].args.polling == PollingType.ALL
    assert f['pod_shards_default_polling_any'].args.polling == PollingType.ANY
    assert f['pod_replicas_shards_manual_polling_any'].args.polling == PollingType.ANY
    assert f['pod_replicas_shards_manual_polling_all'].args.polling == PollingType.ALL


def test_flow_change_parameters():
    class MyExec(Executor):
        @requests
        def foo(self, **kwargs):
            return {'a': 1}

    f = Flow().add(uses=MyExec)
    with f:
        r = f.post('/', parameters={'a': 2}, return_results=True)
        assert r[0].parameters['a'] == 1.0
        r = f.post('/', parameters={}, return_results=True)
        assert r[0].parameters['a'] == 1.0


def test_flow_load_executor_yaml_extra_search_paths():
    f = Flow(extra_search_paths=[os.path.join(cur_dir, 'executor')]).add(
        uses='config.yml'
    )
    with f:
        r = f.post('/', inputs=Document(), return_results=True)
    assert r[0].docs[0].text == 'done'


def test_flow_load_yaml_extra_search_paths():
    f = Flow.load_config(os.path.join(cur_dir, 'flow/flow.yml'))
    with f:
        r = f.post('/', inputs=Document(), return_results=True)
    assert r[0].docs[0].text == 'done'


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
@pytest.mark.parametrize('grpc_data_requests', [True, False])
def test_gateway_only_flows_no_error(capsys, protocol, grpc_data_requests):
    f = Flow(grpc_data_requests=grpc_data_requests, protocol=protocol)
    with f:
        pass
    captured = capsys.readouterr()
    assert not captured.err
