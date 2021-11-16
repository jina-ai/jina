import os

import pytest

from jina.clients.request import request_generator
from jina.helper import get_internal_ip
from jina.parsers import set_gateway_parser
from jina.parsers import set_pod_parser
from jina.peapods import Pod
from jina import (
    __default_executor__,
    __default_host__,
    Executor,
    requests,
    Document,
    DocumentArray,
)
from jina.peapods.networking import GrpcConnectionPool
from jina.types.message import Message
from tests.unit.test_helper import MyDummyExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def pod_args():
    args = [
        '--name',
        'test',
        '--replicas',
        '2',
        '--host',
        __default_host__,
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture
def graph_description():
    return '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'


@pytest.fixture(scope='function')
def pod_args_singleton():
    args = [
        '--name',
        'test2',
        '--uses-before',
        __default_executor__,
        '--replicas',
        '1',
        '--host',
        __default_host__,
    ]
    return set_pod_parser().parse_args(args)


def test_name(pod_args):
    with Pod(pod_args) as pod:
        assert pod.name == 'test'


def test_host(pod_args):
    with Pod(pod_args) as pod:
        assert pod.host == __default_host__
        assert pod.head_host == __default_host__


def test_is_ready(pod_args):
    with Pod(pod_args) as pod:
        assert pod.is_ready is True


def test_equal(pod_args, pod_args_singleton):
    pod1 = Pod(pod_args)
    pod2 = Pod(pod_args)
    assert pod1 == pod2
    pod1.close()
    pod2.close()
    # test not equal
    pod1 = Pod(pod_args)
    pod2 = Pod(pod_args_singleton)
    assert pod1 != pod2
    pod1.close()
    pod2.close()


class ChildDummyExecutor(MyDummyExecutor):
    pass


class ChildDummyExecutor2(MyDummyExecutor):
    pass


def test_uses_before_after(pod_args):
    pod_args.replicas = 1
    pod_args.uses_before = 'MyDummyExecutor'
    pod_args.uses_after = 'ChildDummyExecutor2'
    pod_args.uses = 'ChildDummyExecutor'
    with Pod(pod_args) as pod:
        assert (
            pod.head_args.uses_before_address
            == f'{pod.uses_before_args.host}:{pod.uses_before_args.port_in}'
        )
        assert (
            pod.head_args.uses_after_address
            == f'{pod.uses_after_args.host}:{pod.uses_after_args.port_in}'
        )
        assert pod.num_peas == 4


def test_mermaid_str_no_error(pod_args):
    pod_args.replicas = 3
    pod_args.uses_before = 'MyDummyExecutor'
    pod_args.uses_after = 'ChildDummyExecutor2'
    pod_args.uses = 'ChildDummyExecutor'
    pod = Pod(pod_args)
    print(pod._mermaid_str)


@pytest.mark.slow
@pytest.mark.parametrize('replicas', [1, 2, 4])
def test_pod_context_replicas(replicas):
    args_list = ['--replicas', str(replicas)]
    args = set_pod_parser().parse_args(args_list)
    with Pod(args) as bp:

        if replicas == 1:
            assert bp.num_peas == 2
        else:
            # count head
            assert bp.num_peas == replicas + 1

    Pod(args).start().close()


class AppendNameExecutor(Executor):
    def __init__(self, runtime_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = runtime_args['name']

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=str(self.name)))
        return docs


@pytest.mark.slow
def test_pod_activates_replicas():
    args_list = ['--replicas', '3']
    args = set_pod_parser().parse_args(args_list)
    args.uses = 'AppendNameExecutor'
    with Pod(args) as pod:
        assert pod.num_peas == 4
        response_texts = set()
        # replicas are used in a round robin fashion, so sending 3 requests should hit each one time
        for _ in range(3):
            response = GrpcConnectionPool.send_messages_sync(
                [_create_test_data_message()],
                f'{pod.head_args.host}:{pod.head_args.port_in}',
            )
            response_texts.update(response.response.docs.texts)
        assert all(text in response_texts for text in ['0', '1', '2', 'client'])

    Pod(args).start().close()


@pytest.mark.slow
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='for unknown reason, this test is flaky on Github action, '
    'but locally it SHOULD work fine',
)
@pytest.mark.parametrize(
    'protocol, runtime_cls',
    [
        ('grpc', 'GRPCGatewayRuntime'),
    ],
)
def test_gateway_pod(protocol, runtime_cls, graph_description):
    args = set_gateway_parser().parse_args(
        [
            '--graph-description',
            graph_description,
            '--pods-addresses',
            '{"pod0": ["0.0.0.0:1234"]}',
            '--protocol',
            protocol,
        ]
    )
    with Pod(args) as p:
        assert len(p.all_args) == 1
        assert p.all_args[0].runtime_cls == runtime_cls

    Pod(args).start().close()


def test_pod_naming_with_replica():
    args = set_pod_parser().parse_args(['--name', 'pod', '--replicas', '2'])
    with Pod(args) as bp:
        assert bp.head_pea.name == 'pod/head-0'
        assert bp.replica_set._peas[0].name == 'pod/rep-0'
        assert bp.replica_set._peas[1].name == 'pod/rep-1'


def test_pod_args_remove_uses_ba():
    args = set_pod_parser().parse_args([])
    with Pod(args) as p:
        assert p.num_peas == 2

    args = set_pod_parser().parse_args(
        ['--uses-before', __default_executor__, '--uses-after', __default_executor__]
    )
    with Pod(args) as p:
        assert p.num_peas == 2

    args = set_pod_parser().parse_args(
        [
            '--uses-before',
            __default_executor__,
            '--uses-after',
            __default_executor__,
            '--replicas',
            '2',
        ]
    )
    with Pod(args) as p:
        assert p.num_peas == 3


@pytest.mark.parametrize(
    'pod_host, pea1_host, expected_host_in, expected_host_out',
    [
        (__default_host__, '0.0.0.1', get_internal_ip(), get_internal_ip()),
        ('0.0.0.1', '0.0.0.2', '0.0.0.1', '0.0.0.1'),
        ('0.0.0.1', __default_host__, '0.0.0.1', '0.0.0.1'),
    ],
)
def test_pod_remote_pea_replicas_pea_host_set_partially(
    pod_host,
    pea1_host,
    expected_host_in,
    expected_host_out,
):
    args = set_pod_parser().parse_args(
        ['--peas-hosts', f'{pea1_host}', '--replicas', str(2), '--host', pod_host]
    )
    assert args.host == pod_host
    pod = Pod(args)
    for k, v in pod.peas_args.items():
        if k in ['head', 'tail']:
            assert v.host == args.host
        elif v is not None:
            for pea_arg in v:
                if pea_arg.pea_id in (0, 1):
                    assert pea_arg.host == pea1_host
                else:
                    assert pea_arg.host == args.host


@pytest.mark.parametrize(
    'pod_host, peas_hosts, expected_host_in, expected_host_out',
    [
        (
            __default_host__,
            ['0.0.0.1', '0.0.0.2'],
            get_internal_ip(),
            get_internal_ip(),
        ),
        ('0.0.0.1', ['0.0.0.2', '0.0.0.3'], '0.0.0.1', '0.0.0.1'),
        ('0.0.0.1', [__default_host__, '0.0.0.2'], '0.0.0.1', '0.0.0.1'),
    ],
)
def test_pod_remote_pea_replicas_pea_host_set_completely(
    pod_host,
    peas_hosts,
    expected_host_in,
    expected_host_out,
):
    args = set_pod_parser().parse_args(
        [
            '--peas-hosts',
            f'{peas_hosts[0]}',
            f'{peas_hosts[1]}',
            '--replicas',
            str(2),
            '--host',
            pod_host,
        ]
    )
    assert args.host == pod_host
    pod = Pod(args)
    for k, v in pod.peas_args.items():
        if k in ['head', 'tail']:
            assert v.host == args.host
        elif v is not None:
            for pea_arg, pea_host in zip(v, peas_hosts):
                assert pea_arg.host == pea_host


@pytest.mark.parametrize('replicas', [1])
@pytest.mark.parametrize(
    'upload_files',
    [[os.path.join(cur_dir, __file__), os.path.join(cur_dir, '__init__.py')]],
)
@pytest.mark.parametrize(
    'uses, uses_before, uses_after, py_modules, expected',
    [
        (
            os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            '',
            '',
            [
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, '__init__.py'),
            ],
            [
                os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, __file__),
                os.path.join(cur_dir, '__init__.py'),
            ],
        ),
        (
            os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
            os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            [
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            ],
            [
                os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, __file__),
                os.path.join(cur_dir, '__init__.py'),
            ],
        ),
        (
            'non_existing1.yml',
            'non_existing3.yml',
            'non_existing4.yml',
            ['non_existing1.py', 'non_existing2.py'],
            [os.path.join(cur_dir, __file__), os.path.join(cur_dir, '__init__.py')],
        ),
    ],
)
def test_pod_upload_files(
    replicas,
    upload_files,
    uses,
    uses_before,
    uses_after,
    py_modules,
    expected,
):
    args = set_pod_parser().parse_args(
        [
            '--uses',
            uses,
            '--uses-before',
            uses_before,
            '--uses-after',
            uses_after,
            '--py-modules',
            *py_modules,
            '--upload-files',
            *upload_files,
            '--replicas',
            str(replicas),
        ]
    )
    pod = Pod(args)
    for k, v in pod.peas_args.items():
        if k in ['head', 'tail']:
            if v:
                pass
                # assert sorted(v.upload_files) == sorted(expected)
        elif v is not None and k == 'peas':
            for pea in v:
                print(sorted(pea.upload_files))
                print(sorted(expected))
                assert sorted(pea.upload_files) == sorted(expected)


def _create_test_data_message():
    req = list(request_generator('/', DocumentArray([Document(text='client')])))[0]
    msg = Message(None, req)
    return msg
