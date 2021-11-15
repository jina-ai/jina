import os

import docker
import pytest
from pytest_kind import KindCluster

from jina.logging.logger import JinaLogger

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


class KindClusterWrapper:
    def __init__(self, kind_cluster: KindCluster, logger: JinaLogger):
        self._cluster = kind_cluster
        self._cluster.ensure_kubectl()
        self._kube_config_path = os.path.join(
            os.getcwd(), '.pytest-kind/pytest-kind/kubeconfig'
        )
        self._log = logger
        self._set_kube_config()

    def _set_kube_config(self):
        self._log.debug(f'Setting KUBECONFIG to {self._kube_config_path}')
        os.environ['KUBECONFIG'] = self._kube_config_path

    def load_docker_images(self, images):
        images.append('jinaai/jina:test-pip')
        for image in images:
            self._cluster.load_docker_image(image)


@pytest.fixture()
def logger():
    logger = JinaLogger('kubernetes-testing')
    return logger


@pytest.fixture
def k8s_cluster(kind_cluster: KindCluster, logger: JinaLogger) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, logger)


@pytest.fixture
def docker_image(request):
    image_name, image_tag = request.param
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
    os.environ['JINA_K8S_USE_TEST_PIP'] = 'True'
    yield
    del os.environ['JINA_K8S_USE_TEST_PIP']
