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


@pytest.fixture(scope='function')
def docker_image():
    def _filter_repo_tag(image, image_name='jinahub/pod.dummy_mwu_encoder'):
        tags = image.attrs['RepoTags'] if 'RepoTags' in image.attrs else None
        if tags:
            return tags[0].startswith(image_name)
        else:
            return False

    client = docker.from_env()
    images = client.images.list()
    image_name = list(filter(lambda image: _filter_repo_tag(image), images))[0]

    return image_name


def test_hub_build_level_pass(monkeypatch, test_workspace, docker_image):
    args = set_hub_build_parser().parse_args(
        ['path/hub-mwu', '--push', '--host-info', '--test-level', 'EXECUTOR']
    )
    expected_failed_levels = []

    _, failed_levels = HubIO(args)._test_build(
        docker_image,
        BuildTestLevel.EXECUTOR,
        os.path.join(cur_dir, 'yaml/test-joint.yml'),
        60000,
        True,
        JinaLogger('unittest'),
    )

    assert expected_failed_levels == failed_levels


def test_hub_build_level_fail(monkeypatch, test_workspace, docker_image):
    args = set_hub_build_parser().parse_args(
        ['path/hub-mwu', '--push', '--host-info', '--test-level', 'FLOW']
    )
    expected_failed_levels = [BuildTestLevel.POD_DOCKER, BuildTestLevel.FLOW]

    _, failed_levels = HubIO(args)._test_build(
        docker_image,
        BuildTestLevel.FLOW,
        os.path.join(cur_dir, 'yaml/test-joint.yml'),
        60000,
        True,
        JinaLogger('unittest'),
    )

    assert expected_failed_levels == failed_levels
