from unittest.mock import Mock
from jina.peapods.pods.k8slib.kubernetes_deployment import kubernetes_tools


from jina import Flow


def test_custom_resource_dir():
    mock_create = Mock()
    kubernetes_tools.create = mock_create
    custom_resource_dir = '/test'

    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(name='test_executor', k8s_custom_resource_dir=custom_resource_dir)
    flow.start()

    for call in mock_create.call_args_list:
        assert call[1]['custom_resource_dir'] == custom_resource_dir
