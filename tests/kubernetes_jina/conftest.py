# Contains reusable fixtures for the kubernetes testing module
import os
import pytest
import docker
from pytest_kind import KindCluster

from jina.logging.logger import JinaLogger

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


@pytest.fixture()
def logger():
    logger = JinaLogger('kubernetes-testing')
    return logger


@pytest.fixture()
def executor_image(logger: JinaLogger):
    image, build_logs = client.images.build(path=os.path.join(cur_dir, 'test-executor'), tag='test-executor:0.4.0')
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image.tags[-1]


@pytest.fixture()
def k8s_cluster(kind_cluster) -> KindCluster:
    # TODO: Make more robust
    kind_cluster.kubectl_path = '/usr/local/bin/kubectl'
    os.environ['KUBECONFIG'] = os.path.join(os.getcwd(), '.pytest-kind/pytest-kind/kubeconfig')
    return kind_cluster
