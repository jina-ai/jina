import os
import time
import pytest

from jina.excepts import RuntimeFailToStart
from jina.parsers import set_pea_parser
from jina.peapods.peas.container import ContainerPea

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def env_checker_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'env-checker/'), tag='env-checker')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


def test_container_pea_pass_envs(env_checker_docker_image_built):
    import docker

    with ContainerPea(
        set_pea_parser().parse_args(
            [
                '--uses',
                'docker://env-checker',
                '--env',
                'key1=value1',
                '--env',
                'key2=value2',
            ]
        )
    ) as pea:
        status = pea._container.status

    assert status == 'created'
    client = docker.from_env()
    containers = client.containers.list()
    assert pea._container.id not in containers


def test_container_pea_set_shard_pea_id():
    args = set_pea_parser().parse_args(['--shard-id', '1', '--shards', '3'])

    pea = ContainerPea(args)
    assert pea.args.shard_id == 1
    assert pea.args.pea_id == 1

    assert pea.args.shards == 3
    assert pea.args.parallel == 3


@pytest.fixture(scope='module')
def fail_start_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'fail-start/'), tag='fail-start')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


def test_failing_executor(fail_start_docker_image_built):
    import docker

    args = set_pea_parser().parse_args(
        [
            '--uses',
            'docker://fail-start',
        ]
    )

    with pytest.raises(RuntimeFailToStart):
        pea = ContainerPea(args)
        with pea:
            pass

    client = docker.from_env()
    containers = client.containers.list()
    assert pea._container.id not in containers


def test_pass_arbitrary_kwargs(monkeypatch, mocker):
    import docker

    mock = mocker.Mock()

    mocker.patch(
        'jina.peapods.runtimes.asyncio.AsyncNewLoopRuntime.is_ready',
        return_value=True,
    )

    class MockContainers:
        class MockContainer:
            def reload(self):
                pass

            def logs(self, **kwargs):
                return []

            @property
            def id(self):
                return 'mock-id'

            def reload(self):
                pass

            def kill(self, signal, *args):
                assert signal == 'SIGTERM'

        def __init__(self):
            pass

        def list(self):
            return []

        def get(self, *args):
            return MockContainers.MockContainer()

        def run(self, *args, **kwargs):
            mock_kwargs = {k: kwargs[k] for k in ['hello', 'environment']}
            assert 'ports' in kwargs
            assert 'environment' in kwargs
            envs = kwargs['environment']
            assert 'JINA_LOG_ID' in envs
            assert 'JINA_POD_NAME' in envs
            assert 'VAR1' in envs
            assert envs['VAR1'] == 'BAR'
            assert 'VAR2' in envs
            assert envs['VAR2'] == 'FOO'
            assert 'hello' in kwargs
            assert kwargs['hello'] == 0
            del mock_kwargs['environment']['JINA_LOG_ID']
            mock(**mock_kwargs)
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
            '--env',
            '--env',
            'VAR1=BAR',
            '--env',
            'VAR2=FOO',
            '--docker-kwargs',
            'hello: 0',
        ]
    )
    expected_args = {
        'hello': 0,
        'environment': {'JINA_POD_NAME': 'ContainerPea', 'VAR1': 'BAR', 'VAR2': 'FOO'},
    }
    with ContainerPea(args):
        pass

    mock.assert_called_with(**expected_args)
