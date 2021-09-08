from typing import Dict, Tuple
from unittest.mock import Mock

import pytest
from argparse import Namespace

from jina.logging.logger import JinaLogger
from jina.peapods.pods.k8slib import kubernetes_deployment, kubernetes_tools
from jina.peapods.pods.k8slib.kubernetes_deployment import get_cli_params


@pytest.mark.parametrize(
    ['name', 'dns_name'],
    [
        ('test_pod', 'test-pod'),
        ('test/pod', 'test-pod'),
        ('', ''),
        ('test_pod/2', 'test-pod-2'),
        ('test_pod-0', 'test-pod-0'),
    ],
)
def test_to_dns_name(name: str, dns_name: str):
    assert kubernetes_deployment.to_dns_name(name) == dns_name


@pytest.mark.parametrize(
    ['init_container', 'custom_resource'],
    [(None, None), ({'test-init-arg': 'test-value'}, None), (None, '/test')],
)
def test_deploy_service(init_container: Dict, custom_resource: str):
    kubernetes_tools.create = Mock()

    service_name = kubernetes_deployment.deploy_service(
        name='test-executor',
        namespace='test-ns',
        image_name='test-image',
        container_cmd='test-cmd',
        container_args='test-args',
        logger=JinaLogger('test'),
        replicas=1,
        pull_policy='test-pull-policy',
        init_container=init_container,
        custom_resource_dir=custom_resource,
    )

    assert kubernetes_tools.create.call_count == 2

    service_call_args = kubernetes_tools.create.call_args_list[0][0]
    service_call_kwargs = kubernetes_tools.create.call_args_list[0][1]

    assert service_call_args[0] == 'service'
    assert service_call_kwargs['custom_resource_dir'] == custom_resource

    deployment_call_args = kubernetes_tools.create.call_args_list[1][0]
    deployment_call_kwargs = kubernetes_tools.create.call_args_list[1][1]
    assert deployment_call_kwargs['custom_resource_dir'] == custom_resource

    if init_container:
        assert deployment_call_args[0] == 'deployment-init'
        for k, v in init_container.items():
            assert deployment_call_args[1][k] == v
    else:
        assert deployment_call_args[0] == 'deployment'

    assert service_name == 'test-executor.test-ns.svc.cluster.local'


@pytest.mark.parametrize(
    ['namespace', 'skip_attr', 'expected_string'],
    [
        (
            {
                'some_attribute': 'some_value',
            },
            (),
            '"--some-attribute", "some_value"',
        ),
        (
            {'some_attribute': 'some_value', 'skip_this': 'some_value'},
            ('skip_this',),
            '"--some-attribute", "some_value"',
        ),
        (
            {'uses': 'some_value', 'some_attribute': 'some_value'},
            (),
            '"--some-attribute", "some_value"',
        ),
        ({'some_flag': True}, (), '"--some-flag"'),
    ],
)
def test_get_cli_params(namespace: Dict, skip_attr: Tuple, expected_string: str):
    base_string = (
        ', "--host", "0.0.0.0", "--port-expose", "8080", "--port-in",'
        ' "8081", "--port-out", "8082", "--port-ctrl", "8083"'
    )
    namespace = Namespace(**namespace)

    params = get_cli_params(namespace, skip_attr)

    assert params == expected_string + base_string
