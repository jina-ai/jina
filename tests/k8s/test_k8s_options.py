import os
import pytest

from jina.peapods.pods.config.k8slib.kubernetes_tools import _get_yaml
from jina import Flow

cur_dir = os.path.dirname(__file__)

# TODO: make them a unittest for the yaml generated from K8sPodConfig


def test_default_k8s_connection_pooling(tmpdir):
    flow = Flow(
        name='test-flow',
        port_expose=8080,
        protocol='http',
    ).add(name='test_executor')

    flow.to_k8s_yaml(output_base_path=str(tmpdir), k8s_namespace='test-flow-ns')
    # TODO: assert something here


@pytest.mark.parametrize('k8s_connection_pool', [False, True])
@pytest.mark.parametrize('docker_images', [['jinaai/jina']], indirect=True)
def test_disable_k8s_connection_pooling(k8s_connection_pool, docker_images, tmpdir):
    flow = (
        Flow(name='test-flow', port_expose=8080)
        .add(name='test_executor1', replicas=3)
        .add(name='test_executor2')
    )

    flow.to_k8s_yaml(
        output_base_path=str(tmpdir), k8s_connection_pool=k8s_connection_pool
    )

    # TODO: assert something here


def test_template_file_read_correctly():
    content = _get_yaml('namespace', params={})
    assert 'Test' in content
