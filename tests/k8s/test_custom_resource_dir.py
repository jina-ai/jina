from unittest.mock import Mock
import os

import pytest

from jina.peapods.pods.k8slib.kubernetes_deployment import kubernetes_tools
import kubernetes

from jina import Flow


@pytest.fixture()
def custom_resource_dir(test_dir: str) -> str:
    return os.path.join(test_dir, 'custom-resource')


def test_custom_resource_dir():
    mock_create = Mock()
    kubernetes_tools.create = mock_create
    custom_resource_dir = '/test'

    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(name='test_executor', k8s_custom_resource_dir=custom_resource_dir)
    flow.start()

    # first three calls are for the executor the rest are calls for the gateway
    for call in mock_create.call_args_list[:3]:
        assert call[1]['custom_resource_dir'] == custom_resource_dir


def test_no_resource_dir_specified():
    mock_create = Mock()
    kubernetes_tools.create = mock_create

    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(name='test_executor')
    flow.start()

    for call in mock_create.call_args_list:
        assert call[1]['custom_resource_dir'] is None


def test_template_file_read_correctly(custom_resource_dir: str):
    mock_utils = Mock()
    os.remove = Mock()
    kubernetes.utils.create_from_yaml = mock_utils

    kubernetes_tools.create(
        'namespace', params={}, custom_resource_dir=custom_resource_dir
    )

    mock_utils.assert_called_once()
    path = mock_utils.mock_calls[0][1][1]
    with open(path, 'r') as file:
        lines = file.readlines()
    assert any(['Test' in line for line in lines])
    os.unlink(path)
