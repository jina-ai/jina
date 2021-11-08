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

    def load_docker_image(self, image_name: str):
        self._cluster.load_docker_image(image_name)


@pytest.fixture()
def logger():
    logger = JinaLogger('kubernetes-testing')
    return logger


@pytest.fixture()
def test_dir() -> str:
    return cur_dir


@pytest.fixture()
def k8s_cluster(kind_cluster: KindCluster, logger: JinaLogger) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, logger)


@pytest.fixture()
def reload_executor_image(logger: JinaLogger):
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, 'reload-executor'), tag='reload-executor:0.13.1'
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture()
def test_executor_image(logger: JinaLogger):
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, 'test-executor'), tag='test-executor:0.13.1'
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture()
def executor_merger_image(logger: JinaLogger):
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, 'executor-merger'), tag='merger-executor:0.1.1'
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture()
def dummy_dumper_image(logger: JinaLogger):
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, 'dummy-dumper'), tag='dummy-dumper:0.1.1'
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture()
def slow_process_executor_image(logger: JinaLogger):
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, 'slow-process-executor'),
        tag='slow-process-executor:0.14.1',
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture()
def slow_init_executor_image(logger: JinaLogger):
    image, build_logs = client.images.build(
        path=os.path.join(cur_dir, 'slow-init-executor'),
        tag='slow-init-executor:0.13.1',
    )
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture()
def load_images_in_kind(
    logger,
    test_executor_image,
    executor_merger_image,
    dummy_dumper_image,
    reload_executor_image,
    slow_process_executor_image,
    slow_init_executor_image,
    k8s_cluster,
):
    logger.debug(f'Loading docker image into kind cluster...')
    for image in [
        test_executor_image,
        executor_merger_image,
        dummy_dumper_image,
        reload_executor_image,
        slow_process_executor_image,
        slow_init_executor_image,
        'jinaai/jina:test-pip',
    ]:
        k8s_cluster.load_docker_image(image)
    logger.debug(f'Done loading docker image into kind cluster...')


@pytest.fixture()
def set_test_pip_version():
    import os

    os.environ['JINA_K8S_USE_TEST_PIP'] = 'True'
    yield
    del os.environ['JINA_K8S_USE_TEST_PIP']
