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


# TODO: Can we get jina image to build here as well?
@pytest.fixture(scope='session' ,autouse=True)
def build_and_load_images(k8s_cluster: KindClusterWrapper) -> None:
    CUR_DIR = Path(__file__).parent
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'reload-executor'), 'reload-executor', 'test-pip')
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'test-executor'), 'test-executor', 'test-pip')
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'slow-process-executor'), 'slow-process-executor', 'test-pip')
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'executor-merger'), 'executor-merger', 'test-pip')
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'set-text-executor'), 'set-text-executor', 'test-pip')

    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'failing-executor'), 'failing-executor', 'test-pip')
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'custom-gateway'), 'custom-gateway', 'test-pip')
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'test-stateful-executor'), 'test-stateful-executor', 'test-pip')
    k8s_cluster.build_and_load_docker_image(str(CUR_DIR / 'multiprotocol-gateway'), 'multiprotocol-gateway', 'test-pip')

    k8s_cluster.load_docker_image(image_repo_name='jinaai/jina', tag='test-pip')
    os.environ['JINA_GATEWAY_IMAGE'] = 'jinaai/jina:test-pip'
    yield
    del os.environ['JINA_GATEWAY_IMAGE']
    #k8s_cluster.remove_docker_image('reload-executor', 'test-pip')
    #k8s_cluster.remove_docker_image('test-executor', 'test-pip')
    #k8s_cluster.remove_docker_image('slow-process-executor', 'test-pip')
    #k8s_cluster.remove_docker_image('executor-merger', 'test-pip')
    #k8s_cluster.remove_docker_image('set-text-executor', 'test-pip')

    #k8s_cluster.remove_docker_image('failing-executor', 'test-pip')
    #k8s_cluster.remove_docker_image('custom-gateway', 'test-pip')
    #k8s_cluster.remove_docker_image('test-stateful-executor', 'test-pip')
    #k8s_cluster.remove_docker_image('multiprotocol-gateway', 'test-pip')


@pytest.fixture(scope='session')
def k8s_cluster(kind_cluster: KindCluster) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, JinaLogger('kubernetes-cluster-logger'))

## END OF NEW

@pytest.fixture()
def test_dir() -> str:
    return cur_dir


@pytest.fixture
def logger() -> JinaLogger:
    return JinaLogger('kubernetes-testing')


@pytest.fixture(scope='session')
def k8s_cluster(kind_cluster: KindCluster) -> KindClusterWrapper:
    return KindClusterWrapper(kind_cluster, JinaLogger('kubernetes-cluster-logger'))


@pytest.fixture
def image_name_tag_map() -> Dict[str, str]:
    return {
        'reload-executor': 'test-pip',
        'test-executor': 'test-pip',
        'slow-process-executor': 'test-pip',
        'executor-merger': 'test-pip',
        'set-text-executor': 'test-pip',
        'failing-executor': 'test-pip',
        'jinaai/jina': 'test-pip',
        'custom-gateway': 'test-pip',
        'test-stateful-executor': 'test-pip',
        'multiprotocol-gateway': 'test-pip',
    }


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
