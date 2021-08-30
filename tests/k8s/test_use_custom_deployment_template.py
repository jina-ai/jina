# Unit tests for custom deployment templates
from jina import Flow
from jina.peapods.pods.k8slib.kubernetes_deployment import kubernetes_tools

import pytest


class KubernetesCreateMock:

    def __init__(self):
        self.call_count = 0
        self.call_args = []
        self.call_kwargs = []

    def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args.append(args)
        self.call_kwargs.append(kwargs)


@pytest.fixture(scope='function')
def patch_kubernetes_deploy(monkeypatch):
    mock = KubernetesCreateMock()
    monkeypatch.setattr(kubernetes_tools, 'create', mock)
    return mock


def test_args_parse_correctly(custom_deployment_template_dir: str, patch_kubernetes_deploy):
    custom_args = {
        'k8s_yml_template_dir': custom_deployment_template_dir,
        'k8s_yml_template_args': {
            'limit_cpu': 1,
            'request_cpu': 0.5
        }
    }
    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(
        name='test_executor',
        k8s_custom_deployment_args=custom_args
    )
    flow.start()

    assert patch_kubernetes_deploy.call_count == 6

    executor_call_kwargs = patch_kubernetes_deploy.call_kwargs[0]
    k8s_yml_template_args = executor_call_kwargs.get('custom_deployment_config')

    assert k8s_yml_template_args.__dict__ == custom_args
