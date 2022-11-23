import contextlib
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict

import docker
import pytest
from pytest_kind import KindCluster, cluster

from jina.logging.logger import JinaLogger
from tests.k8s.kind_wrapper import KindClusterWrapper

client = docker.from_env()
cur_dir = os.path.dirname(__file__)
cluster.KIND_VERSION = 'v0.11.1'

IMAGE_DIR = Path(__file__).parent / 'images'
IMAGES: List[str] = [
    'reload-executor',
    'test-executor',
    'slow-process-executor',
    'executor-merger',
    'set-text-executor',
    'failing-executor',
    'custom-gateway',
    'test-stateful-executor',
    'multiprotocol-gateway',
]

# TODO: Can we get jina image to build here as well?
@pytest.fixture(scope='session' ,autouse=True)
def build_and_load_images(k8s_cluster: KindClusterWrapper) -> None:
    for image in IMAGES:
        k8s_cluster.build_and_load_docker_image(str(IMAGE_DIR / image), image, 'test-pip')

    k8s_cluster.load_docker_image(image_repo_name='jinaai/jina', tag='test-pip')
    os.environ['JINA_GATEWAY_IMAGE'] = 'jinaai/jina:test-pip'
    yield
    del os.environ['JINA_GATEWAY_IMAGE']
    for image in IMAGES:
        k8s_cluster.remove_docker_image(image, 'test-pip')

@pytest.fixture(scope='session')
def k8s_cluster(kind_cluster: KindCluster) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, JinaLogger('kubernetes-cluster-logger'))


@pytest.fixture
def logger() -> JinaLogger:
    return JinaLogger('kubernetes-testing')


@pytest.fixture(scope='session')
def k8s_cluster(kind_cluster: KindCluster) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, JinaLogger('kubernetes-cluster-logger'))


@pytest.fixture(autouse=True)
def load_cluster_config(k8s_cluster: KindClusterWrapper) -> None:
    import kubernetes

    try:
        # try loading kube config from disk first
        kubernetes.config.load_kube_config()
    except kubernetes.config.config_exception.ConfigException:
        # if the config could not be read from disk, try loading in cluster config
        # this works if we are running inside k8s
        kubernetes.config.load_incluster_config()


@contextlib.contextmanager
def shell_portforward(
    kubectl_path, pod_or_service, port1, port2, namespace, waiting: float = 1
):
    try:
        proc = subprocess.Popen(
            [
                kubectl_path,
                'port-forward',
                pod_or_service,
                f'{port1}:{port2}',
                '--namespace',
                namespace,
            ]
        )
        # Go and the port-forwarding needs some ms to be ready
        time.sleep(waiting)

        yield None
        time.sleep(waiting)

    except Exception as err:
        # Suppress extension exception
        raise OSError(err) from None

    finally:
        proc.kill()

@pytest.fixture
def docker_images(
    request: pytest.FixtureRequest,
    k8s_cluster: KindClusterWrapper,
) -> List[str]:
    image_repos: List[str] = request.param
    return [k8s_cluster.build_and_load_docker_image(str(IMAGE_DIR / image_repo), image_repo,'test-pip') for image_repo in image_repos]
