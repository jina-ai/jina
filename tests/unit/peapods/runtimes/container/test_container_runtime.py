import os
import time
from sys import platform
import multiprocessing

import pytest

from jina.checker import NetworkChecker
from jina.executors import BaseExecutor
from jina.executors.decorators import requests
from jina import Flow
from jina.helper import random_name
from jina.parsers import set_pea_parser
from jina.parsers.ping import set_ping_parser
from jina.peapods import Pea
from jina.peapods.runtimes.container import ContainerRuntime
from tests import random_docs, validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))

img_name = 'jina/mwu-encoder'

defaulthost = '0.0.0.0'
localhost = (
    defaulthost
    if (platform == "linux" or platform == "linux2")
    else 'host.docker.internal'
)


@pytest.fixture
def _logforward():
    class _LogForward(BaseExecutor):
        @requests
        def foo(self, **kwargs):
            pass

    return _LogForward


@pytest.fixture(scope='module')
def docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'mwu-encoder/'), tag=img_name)
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


def test_simple_container(docker_image_built):
    args = set_pea_parser().parse_args(['--uses', f'docker://{img_name}'])

    with Pea(args):
        pass

    time.sleep(2)
    Pea(args).start().close()


def test_flow_with_one_container_pod(docker_image_built):
    f = Flow().add(name='dummyEncoder1', uses=f'docker://{img_name}')

    with f:
        f.post(on='/index', inputs=random_docs(10))


def test_flow_with_replica_container_ext_yaml(docker_image_built):
    f = Flow().add(
        name='dummyEncoder3',
        uses=f'docker://{img_name}',
        parallel=3,
        entrypoint='jina pea',
    )

    with f:
        f.post(on='/index', inputs=random_docs(10))
        f.post(on='/index', inputs=random_docs(10))
        f.post(on='/index', inputs=random_docs(10))


def test_flow_topo1(docker_image_built):
    f = (
        Flow()
        .add(
            name='d0',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
        )
        .add(
            name='d1',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
        )
        .add(
            name='d2',
            uses='docker://jinaai/jina:test-pip',
            needs='d0',
            entrypoint='jina executor',
        )
        .join(['d2', 'd1'])
    )

    with f:
        f.post(on='/index', inputs=random_docs(10))


def test_flow_topo_mixed(docker_image_built, _logforward):
    f = (
        Flow()
        .add(
            name='d4',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
        )
        .add(name='d5', uses=_logforward)
        .add(
            name='d6',
            uses='docker://jinaai/jina:test-pip',
            needs='d4',
            entrypoint='jina executor',
        )
        .join(['d6', 'd5'])
    )

    with f:
        f.post(on='/index', inputs=random_docs(10))


def test_flow_topo_parallel():
    f = (
        Flow()
        .add(
            name='d7',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
            parallel=3,
        )
        .add(name='d8', parallel=3)
        .add(
            name='d9',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
            needs='d7',
        )
        .join(['d9', 'd8'])
    )

    with f:
        f.post(on='/index', inputs=random_docs(10))


def test_flow_topo_ldl_parallel():
    f = (
        Flow()
        .add(name='d10')
        .add(
            name='d11',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
            parallel=3,
        )
        .add(name='d12')
    )

    with f:
        f.post(on='/index', inputs=random_docs(10))


def test_container_ping(docker_image_built):
    a4 = set_pea_parser().parse_args(['--uses', f'docker://{img_name}'])
    a5 = set_ping_parser().parse_args(
        ['0.0.0.0', str(a4.port_ctrl), '--print-response']
    )

    # test with container
    with pytest.raises(SystemExit) as cm:
        with Pea(a4):
            NetworkChecker(a5)

    assert cm.value.code == 0


def test_tail_host_docker2local_parallel():
    f = (
        Flow()
        .add(
            name='d10',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
            parallel=3,
        )
        .add(name='d11')
    )
    with f:
        assert getattr(f._pod_nodes['d10'].peas_args['tail'], 'host_out') == defaulthost


def test_tail_host_docker2local():
    f = (
        Flow()
        .add(
            name='d12',
            uses='docker://jinaai/jina:test-pip',
            entrypoint='jina executor',
        )
        .add(name='d13')
    )
    with f:
        assert getattr(f._pod_nodes['d12'].tail_args, 'host_out') == localhost


def test_pass_arbitrary_kwargs(monkeypatch, mocker):
    import docker

    mock = mocker.Mock()
    mocker.patch(
        'jina.peapods.runtimes.container.ContainerRuntime.is_ready',
        return_value=True,
    )

    class MockContainers:
        class MockContainer:
            def reload(self):
                pass

            def logs(self, **kwargs):
                return []

        def __init__(self):
            pass

        def run(self, *args, **kwargs):
            mock_kwargs = {k: kwargs[k] for k in ['hello', 'ports', 'environment']}
            mock(**mock_kwargs)
            assert 'ports' in kwargs
            assert kwargs['ports'] is None
            assert 'environment' in kwargs
            assert kwargs['environment'] == ['VAR1=BAR', 'VAR2=FOO']
            assert 'hello' in kwargs
            assert kwargs['hello'] == 0
            return MockContainers.MockContainer()

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

        def version(self):
            return {'Version': '20.0.1'}

        @property
        def networks(self):
            return {'bridge': None}

        @property
        def containers(self):
            return MockContainers()

        @property
        def images(self):
            return {}

    monkeypatch.setattr(docker, 'from_env', MockClient)
    args = set_pea_parser().parse_args(
        [
            '--uses',
            'docker://jinahub/pod',
            '--docker-kwargs',
            'hello: 0',
            'environment: ["VAR1=BAR", "VAR2=FOO"]',
        ]
    )
    _ = ContainerRuntime(args, ctrl_addr='', ready_event=multiprocessing.Event())
    expected_args = {'hello': 0, 'ports': None, 'environment': ['VAR1=BAR', 'VAR2=FOO']}
    mock.assert_called_with(**expected_args)


def test_pass_arbitrary_kwargs_from_yaml():
    f = Flow.load_config(os.path.join(cur_dir, 'flow.yml'))
    assert f._pod_nodes['pod1'].args.docker_kwargs == {
        'hello': 0,
        'environment': ['VAR1=BAR', 'VAR2=FOO'],
    }


def test_container_override_params(docker_image_built, tmpdir, mocker):
    def validate_response(resp):
        assert len(resp.docs) > 0
        for doc in resp.docs:
            assert doc.tags['greetings'] == 'overriden greetings'

    mock = mocker.Mock()

    abc_path = os.path.join(tmpdir, 'abc')
    f = Flow().add(
        name=random_name(),
        uses=f'docker://{img_name}',
        volumes=abc_path + ':' + '/mapped/here/abc',
        uses_with={'greetings': 'overriden greetings'},
        uses_metas={
            'name': 'ext-mwu-encoder',
            'workspace': '/mapped/here/abc',
        },
    )

    with f:
        f.index(random_docs(10), on_done=mock)

    assert os.path.exists(
        os.path.join(abc_path, 'ext-mwu-encoder', '0', 'ext-mwu-encoder.bin')
    )
    validate_callback(mock, validate_response)


def test_container_volume(docker_image_built, tmpdir):
    abc_path = os.path.join(tmpdir, 'abc')
    f = Flow().add(
        name=random_name(),
        uses=f'docker://{img_name}',
        volumes=abc_path + ':' + '/mapped/here/abc',
        uses_metas={
            'name': 'ext-mwu-encoder',
            'workspace': '/mapped/here/abc',
        },
    )

    with f:
        f.index(random_docs(10))

    assert os.path.exists(
        os.path.join(abc_path, 'ext-mwu-encoder', '0', 'ext-mwu-encoder.bin')
    )


@pytest.mark.parametrize(
    (
        'gpus_value',
        'expected_count',
        'expected_device',
        'expected_driver',
        'expected_capabilities',
    ),
    [
        ('all', -1, [], '', [['gpu']]),  # all gpus
        ('2', 2, [], '', [['gpu']]),  # use two gpus
        (
            'device=GPU-fake-gpu-id',
            0,
            ['GPU-fake-gpu-id'],
            '',
            [['gpu']],
        ),  # gpu by one device id
        (
            'device=GPU-fake-gpu-id1,device=GPU-fake-gpu-id2',
            0,
            ['GPU-fake-gpu-id1', 'GPU-fake-gpu-id2'],
            '',
            [['gpu']],
        ),  # gpu by 2 device id
        (
            'device=GPU-fake-gpu-id,driver=nvidia,capabilities=utility,capabilities=display',
            0,
            ['GPU-fake-gpu-id'],
            'nvidia',
            [['gpu', 'utility', 'display']],
        ),  # gpu with id, driver and capability
        (
            'device=GPU-fake-gpu-id1,device=GPU-fake-gpu-id2,driver=nvidia,capabilities=utility',
            0,
            ['GPU-fake-gpu-id1', 'GPU-fake-gpu-id2'],
            'nvidia',
            [['gpu', 'utility']],
        ),  # multiple ids
    ],
)
def test_gpu_container(
    gpus_value, expected_count, expected_device, expected_driver, expected_capabilities
):
    args = set_pea_parser().parse_args(
        ['--uses', f'docker://{img_name}', '--gpus', gpus_value]
    )

    device_requests = ContainerRuntime._get_gpu_device_requests(args.gpus)
    assert device_requests[0]['Count'] == expected_count
    assert device_requests[0]['DeviceIDs'] == expected_device
    assert device_requests[0]['Driver'] == expected_driver
    assert device_requests[0]['Capabilities'] == expected_capabilities
