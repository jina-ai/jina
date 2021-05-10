import os

import docker
import pytest
from jina.docker.hubio import HubIO
from jina.enums import BuildTestLevel
from jina.logging import JinaLogger
from jina.parsers.hub import set_hub_build_parser

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

    img_name = 'jinahub/pod.dummy_mwu_encoder:0.0.6'
    client = docker.from_env()
    client.images.pull(img_name)
    images = client.images.list()
    image_name = list(filter(lambda image: _filter_repo_tag(image), images))[0]
    return image_name

