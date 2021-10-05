import os

from jina.peapods.pods.k8slib.kubernetes_tools import _get_yaml
from jina import Flow


def test_custom_resource_dir():
    custom_resource_dir = '/test'

    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(name='test_executor', k8s_custom_resource_dir=custom_resource_dir)
    assert (
        flow._pod_nodes['test_executor'].args.k8s_custom_resource_dir
        == custom_resource_dir
    )


def test_no_resource_dir_specified():
    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(name='test_executor')
    assert flow._pod_nodes['test_executor'].args.k8s_custom_resource_dir is None


def test_template_file_read_correctly(test_dir: str):
    custom_resource_dir = os.path.join(test_dir, 'custom-resource')
    content = _get_yaml('namespace', params={}, custom_resource_dir=custom_resource_dir)

    assert 'Test' in content
