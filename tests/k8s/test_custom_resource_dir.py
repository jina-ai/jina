from unittest.mock import Mock
import os

from jina.peapods.pods.k8slib.kubernetes_deployment import kubernetes_tools
from jina import Flow


def test_custom_resource_dir(monkeypatch):
    mock_create = Mock()
    monkeypatch.setattr(kubernetes_tools, 'create', mock_create)
    custom_resource_dir = '/test'

    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(name='test_executor', k8s_custom_resource_dir=custom_resource_dir)
    flow.start()

    # first three calls are for the executor the rest are calls for the gateway
    for call in mock_create.call_args_list[:3]:
        assert call[1]['custom_resource_dir'] == custom_resource_dir


def test_no_resource_dir_specified(monkeypatch):
    mock_create = Mock()
    monkeypatch.setattr(kubernetes_tools, 'create', mock_create)

    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(name='test_executor')
    flow.start()

    for call in mock_create.call_args_list:
        assert call[1]['custom_resource_dir'] is None


def test_template_file_read_correctly(test_dir: str):
    custom_resource_dir = os.path.join(test_dir, 'custom-resource')
    content = kubernetes_tools._get_yaml(
        'namespace', params={}, custom_resource_dir=custom_resource_dir
    )

    assert 'Test' in content
