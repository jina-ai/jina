import os
import pytest

from jina.peapods.pods.k8slib.kubernetes_tools import _get_yaml
from jina import Flow


def test_custom_resource_dir():
    custom_resource_dir = '/test'

    flow = Flow(
        name='test-flow',
        port_expose=8080,
        infrastructure='K8S',
        protocol='http',
        k8s_namespace='test-flow-ns',
    ).add(name='test_executor', k8s_custom_resource_dir=custom_resource_dir)
    assert (
        flow._pod_nodes['test_executor'].args.k8s_custom_resource_dir
        == custom_resource_dir
    )


def test_no_resource_dir_specified():
    flow = Flow(
        name='test-flow',
        port_expose=8080,
        infrastructure='K8S',
        protocol='http',
        k8s_namespace='test-flow-ns',
    ).add(name='test_executor')
    assert flow._pod_nodes['test_executor'].args.k8s_custom_resource_dir is None


def test_default_k8s_connection_pooling():
    flow = Flow(
        name='test-flow',
        port_expose=8080,
        infrastructure='K8S',
        k8s_namespace='test-flow-ns',
    ).add(name='test_executor')
    assert flow._pod_nodes['test_executor'].args.k8s_connection_pool


@pytest.mark.parametrize('k8s_connection_pool', [False, True])
def test_disable_k8s_connection_pooling(k8s_connection_pool):
    flow = (
        Flow(
            name='test-flow',
            port_expose=8080,
            infrastructure='K8S',
            k8s_disable_connection_pool=not k8s_connection_pool,
            k8s_namespace='test-flow-ns',
        )
        .add(name='test_executor1', replicas=3)
        .add(name='test_executor2')
    )
    for pod in flow._pod_nodes.values():
        assert pod.args.k8s_connection_pool == k8s_connection_pool
        for peapod in pod.k8s_deployments:
            assert peapod.deployment_args.k8s_connection_pool == k8s_connection_pool


def test_template_file_read_correctly(test_dir: str):
    custom_resource_dir = os.path.join(test_dir, 'custom-resource')
    content = _get_yaml('namespace', params={}, custom_resource_dir=custom_resource_dir)

    assert 'Test' in content
