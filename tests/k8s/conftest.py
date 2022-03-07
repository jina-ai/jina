import os
import subprocess
from pathlib import Path

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
        self._install_linkderd(kind_cluster)
        self._loaded_images = set()

    def _install_linkderd(self, kind_cluster):
        proc = subprocess.Popen(
            [f'{Path.home()}/.linkerd2/bin/linkerd', 'install'],
            stdout=subprocess.PIPE,
            env={"KUBECONFIG": str(kind_cluster.kubeconfig_path)},
        )
        _ = subprocess.check_output(
            (
                str(kind_cluster.kubectl_path),
                'apply',
                '-f',
                '-',
            ),
            stdin=proc.stdout,
            env={"KUBECONFIG": str(kind_cluster.kubeconfig_path)},
        )
        returncode = proc.poll()
        if returncode is not None and returncode != 0:
            raise Exception(f"Installing linkerd failed with {returncode}")

    def _set_kube_config(self):
        self._log.debug(f'Setting KUBECONFIG to {self._kube_config_path}')
        os.environ['KUBECONFIG'] = self._kube_config_path

    def load_docker_images(self, images, image_tag_map):
        for image in images:
            full_image_name = image + ':' + image_tag_map[image]
            if full_image_name not in self._loaded_images:
                if image != 'alpine' and image != 'jinaai/jina':
                    build_docker_image(image, image_tag_map)
                self._cluster.load_docker_image(full_image_name)
                self._loaded_images.add(full_image_name)


@pytest.fixture()
def test_dir() -> str:
    return cur_dir


@pytest.fixture
def logger():
    return JinaLogger('kubernetes-testing')


@pytest.fixture(scope='session')
def k8s_cluster(kind_cluster: KindCluster) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, JinaLogger('kubernetes-cluster-logger'))


@pytest.fixture
def image_name_tag_map():
    return {
        'reload-executor': '0.13.1',
        'test-executor': '0.13.1',
        'slow-process-executor': '0.14.1',
        'executor-merger': '0.1.1',
        'jinaai/jina': 'test-pip',
    }


def build_docker_image(image_name, image_name_tag_map):
    logger = JinaLogger('kubernetes-testing')
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
    os.environ['JINA_K8S_USE_TEST_PIP'] = 'True'
    yield
    del os.environ['JINA_K8S_USE_TEST_PIP']


@pytest.fixture(autouse=True)
def load_cluster_config(k8s_cluster):
    import kubernetes

    try:
        # try loading kube config from disk first
        kubernetes.config.load_kube_config()
    except kubernetes.config.config_exception.ConfigException:
        # if the config could not be read from disk, try loading in cluster config
        # this works if we are running inside k8s
        kubernetes.config.load_incluster_config()


@pytest.fixture
def docker_images(request, image_name_tag_map, k8s_cluster):
    image_names = request.param
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    return images
