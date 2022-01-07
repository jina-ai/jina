import json
import os
from multiprocessing import Process

import pytest

from jina.clients.request import request_generator
from jina.enums import PollingType, PeaRoleType
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


@pytest.mark.slow
@pytest.mark.parametrize('shards', [1, 2, 4])
def test_pod_context_shards_replicas(shards):
    args_list = ['--replicas', str(3)]
    args_list.extend(['--shards', str(shards)])
    args = set_pod_parser().parse_args(args_list)
    with Pod(args) as bp:
        assert bp.num_peas == shards * 3 + 1

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
            response = GrpcConnectionPool.send_request_sync(
                _create_test_data_message(),
                f'{pod.head_args.host}:{pod.head_args.port_in}',
            )
            response_texts.update(response.response.docs.texts)
        assert 4 == len(response_texts)
        assert all(text in response_texts for text in ['0', '1', '2', 'client'])

    Pod(args).start().close()


class AppendParamExecutor(Executor):
    def __init__(self, param, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param = param

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=str(self.param)))
        return docs


@pytest.mark.slow
@pytest.mark.parametrize('shards', [1, 2])
def test_pod_rolling_update(shards):
    args_list = ['--replicas', '7']
    args_list.extend(['--shards', str(shards)])
    args = set_pod_parser().parse_args(args_list)
    args.uses = 'AppendParamExecutor'
    args.uses_with = {'param': 10}
    with Pod(args) as pod:

        async def run_async_test():
            response_texts = await _send_requests(pod)
            assert 2 == len(response_texts)
            assert all(text in response_texts for text in ['10', 'client'])

            await pod.rolling_update(uses_with={'param': 20})
            response_texts = await _send_requests(pod)
            assert 2 == len(response_texts)
            assert all(text in response_texts for text in ['20', 'client'])
            assert '10' not in response_texts

        p = Process(target=run_async_test)
        p.start()
        p.join()
        assert p.exitcode == 0

    Pod(args).start().close()


async def _send_requests(pod):
    response_texts = set()
    for _ in range(3):
        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
        )
        response_texts.update(response.response.docs.texts)
    return response_texts


class AppendShardExecutor(Executor):
    def __init__(self, runtime_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shard_id = runtime_args['shard_id']

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=str(self.shard_id)))
        return docs


def test_pod_naming_with_shards():
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--shards',
            '2',
            '--replicas',
            '3',
        ]
    )
    with Pod(args) as pod:
        assert pod.head_pea.name == 'pod/head-0'

        assert pod.shards[0].args[0].name == 'pod/shard-0/rep-0'
        assert pod.shards[0].args[1].name == 'pod/shard-0/rep-1'
        assert pod.shards[0].args[2].name == 'pod/shard-0/rep-2'

        assert pod.shards[1].args[0].name == 'pod/shard-1/rep-0'
        assert pod.shards[1].args[1].name == 'pod/shard-1/rep-1'
        assert pod.shards[1].args[2].name == 'pod/shard-1/rep-2'


@pytest.mark.slow
def test_pod_activates_shards():
    args_list = ['--replicas', '3']
    args_list.extend(['--shards', '3'])
    args = set_pod_parser().parse_args(args_list)
    args.uses = 'AppendShardExecutor'
    args.polling = PollingType.ALL
    with Pod(args) as pod:
        assert pod.num_peas == 3 * 3 + 1
        response_texts = set()
        # replicas are used in a round robin fashion, so sending 3 requests should hit each one time
        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
        )
        response_texts.update(response.response.docs.texts)
        assert 4 == len(response.response.docs.texts)
        assert 4 == len(response_texts)
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
        assert bp.shards[0]._peas[0].name == 'pod/rep-0'
        assert bp.shards[0]._peas[1].name == 'pod/rep-1'


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
            for shard_id in v:
                for pea_arg in v[shard_id]:
                    if pea_arg.shard_id in (0, 1):
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
            for shard_id in v:
                for pea_arg, pea_host in zip(v[shard_id], peas_hosts):
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
            for shard_id in v:
                for pea in v[shard_id]:
                    print(sorted(pea.upload_files))
                    print(sorted(expected))
                    assert sorted(pea.upload_files) == sorted(expected)


class DynamicPollingExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests(on='/any')
    def any(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs

    @requests(on='/all')
    def all(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs

    @requests(on='/no_polling')
    def no_polling(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs


@pytest.mark.parametrize('polling', ['any', 'all'])
def test_dynamic_polling_with_config(polling):
    endpoint_polling = {'/any': PollingType.ANY, '/all': PollingType.ALL, '*': polling}

    args = set_pod_parser().parse_args(
        [
            '--uses',
            'DynamicPollingExecutor',
            '--shards',
            str(2),
            '--polling',
            json.dumps(endpoint_polling),
        ]
    )
    pod = Pod(args)

    with pod:
        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(endpoint='/all'),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
            endpoint='/all',
        )
        assert len(response.docs) == 1 + 2  # 1 source doc + 2 docs added by each shard

        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(endpoint='/any'),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
            endpoint='/any',
        )
        assert (
            len(response.docs) == 1 + 1
        )  # 1 source doc + 1 doc added by the one shard

        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(endpoint='/no_polling'),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
            endpoint='/no_polling',
        )
        if polling == 'any':
            assert (
                len(response.docs) == 1 + 1
            )  # 1 source doc + 1 doc added by the one shard
        else:
            assert (
                len(response.docs) == 1 + 2
            )  # 1 source doc + 1 doc added by the two shards


class DynamicPollingExecutorDefaultNames(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs


@pytest.mark.parametrize('polling', ['any', 'all'])
def test_dynamic_polling_default_config(polling):
    args = set_pod_parser().parse_args(
        [
            '--uses',
            'DynamicPollingExecutorDefaultNames',
            '--shards',
            str(2),
            '--polling',
            polling,
        ]
    )
    pod = Pod(args)

    with pod:
        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(endpoint='/search'),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
            endpoint='/search',
        )
        assert len(response.docs) == 1 + 2

        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(endpoint='/index'),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
            endpoint='/index',
        )
        assert len(response.docs) == 1 + 1


@pytest.mark.parametrize('polling', ['any', 'all'])
def test_dynamic_polling_overwrite_default_config(polling):
    endpoint_polling = {'/search': PollingType.ANY, '*': polling}
    args = set_pod_parser().parse_args(
        [
            '--uses',
            'DynamicPollingExecutorDefaultNames',
            '--shards',
            str(2),
            '--polling',
            json.dumps(endpoint_polling),
        ]
    )
    pod = Pod(args)

    with pod:
        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(endpoint='/search'),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
            endpoint='/search',
        )
        assert (
            len(response.docs) == 1 + 1
        )  # 1 source doc + 1 doc added by the one shard

        response = GrpcConnectionPool.send_request_sync(
            _create_test_data_message(endpoint='/index'),
            f'{pod.head_args.host}:{pod.head_args.port_in}',
            endpoint='/index',
        )
        assert (
            len(response.docs) == 1 + 1
        )  # 1 source doc + 1 doc added by the one shard


def _create_test_data_message(endpoint='/'):
    return list(request_generator(endpoint, DocumentArray([Document(text='client')])))[
        0
    ]
