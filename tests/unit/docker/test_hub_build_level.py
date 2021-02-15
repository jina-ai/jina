import os

import docker
import pytest
from jina.docker.hubio import HubIO
from jina.enums import BuildTestLevel
from jina.logging import JinaLogger
from jina.parsers.hub import set_hub_build_parser

cli = docker.APIClient(base_url='unix://var/run/docker.sock')
cur_dir = os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope='function')
def test_workspace(tmpdir):
    os.environ['JINA_TEST_JOINT'] = str(tmpdir)
    workspace_path = os.environ['JINA_TEST_JOINT']
    yield workspace_path
    del os.environ['JINA_TEST_JOINT']


def test_hub_build_level_pass(monkeypatch, test_workspace):
    args = set_hub_build_parser().parse_args(['path/hub-mwu', '--push', '--host-info', '--test-level', 'EXECUTOR'])
    docker_image = cli.get_image('jinahub/pod.dummy_mwu_encoder')
    expected_failed_levels = []

    _, failed_levels = HubIO(args)._test_build(docker_image, BuildTestLevel.EXECUTOR, os.path.join(cur_dir, 'yaml/test-joint.yml'), 60, True, JinaLogger('unittest'))

    assert expected_failed_levels == failed_levels


def test_hub_build_level_fail(monkeypatch, test_workspace):
    args = set_hub_build_parser().parse_args(['path/hub-mwu', '--push', '--host-info', '--test-level', 'FLOW'])
    docker_image = cli.get_image('jinahub/pod.dummy_mwu_encoder')
    expected_failed_levels = [BuildTestLevel.POD_NONDOCKER, BuildTestLevel.POD_DOCKER, BuildTestLevel.FLOW]

    _, failed_levels = HubIO(args)._test_build(docker_image, BuildTestLevel.FLOW, os.path.join(cur_dir, 'yaml/test-joint.yml'), 60, True, JinaLogger('unittest'))

    assert expected_failed_levels == failed_levels