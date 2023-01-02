import os

import docker
import pytest

from jina.logging.logger import JinaLogger

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


@pytest.fixture()
def test_dir() -> str:
    return cur_dir


@pytest.fixture
def logger():
    return JinaLogger('docker-compose-testing')


@pytest.fixture
def image_name_tag_map():
    return {
        'reload-executor': '0.13.1',
        'test-executor': '0.13.1',
        'executor-merger': '0.1.1',
        'custom-gateway': '0.1.1',
        'multiprotocol-gateway': '0.1.1',
        'jinaai/jina': 'test-pip',
    }


def build_docker_image(image_name, image_name_tag_map):
    logger = JinaLogger('docker-compose-testing')
    image_tag = image_name + ':' + image_name_tag_map[image_name]
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, image_name), tag=image_tag
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture(autouse=True)
def set_test_pip_version():
    os.environ['JINA_GATEWAY_IMAGE'] = 'jinaai/jina:test-pip'
    yield
    del os.environ['JINA_GATEWAY_IMAGE']


@pytest.fixture(autouse=True)
def build_images(image_name_tag_map):
    for image in image_name_tag_map.keys():
        if image != 'jinaai/jina':
            build_docker_image(image, image_name_tag_map)


@pytest.fixture
def docker_images(request, image_name_tag_map):
    image_names = request.param
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    return images
