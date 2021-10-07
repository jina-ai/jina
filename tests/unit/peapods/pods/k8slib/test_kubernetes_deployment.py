from typing import Dict, Tuple
from unittest.mock import Mock

import pytest
from argparse import Namespace

from jina.logging.logger import JinaLogger
from jina.parsers import set_pod_parser
from jina.peapods.pods.k8s import K8sPod
from jina.peapods.pods.k8slib.kubernetes_deployment import (
    get_cli_params,
    dictionary_to_cli_param,
    get_init_container_args,
    kubernetes_tools,
    to_dns_name,
    deploy_service,
)


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
    assert to_dns_name(name) == dns_name


@pytest.mark.parametrize(
    ['init_container', 'custom_resource'],
    [(None, None), ({'test-init-arg': 'test-value'}, None), (None, '/test')],
)
def test_deploy_service(init_container: Dict, custom_resource: str, monkeypatch):
    mock_create = Mock()
    monkeypatch.setattr(kubernetes_tools, 'create', mock_create)

    service_name = deploy_service(
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
        env={'k1': 'v1', 'k2': 'v2'},
    )

    assert mock_create.call_count == 5

    service_call_args = mock_create.call_args_list[0][0]
    service_call_kwargs = mock_create.call_args_list[0][1]

    assert service_call_args[0] == 'service'
    assert service_call_kwargs['custom_resource_dir'] == custom_resource

    configmap_call_args = mock_create.call_args_list[1][0]
    configmap_call_kwargs = mock_create.call_args_list[1][1]

    assert configmap_call_args[0] == 'configmap'
    assert configmap_call_kwargs['custom_resource_dir'] is None

    deployment_call_args = mock_create.call_args_list[2][0]
    deployment_call_kwargs = mock_create.call_args_list[2][1]
    assert deployment_call_kwargs['custom_resource_dir'] == custom_resource

    if init_container:
        assert deployment_call_args[0] == 'deployment-init'
        for k, v in init_container.items():
            assert deployment_call_args[1][k] == v
    else:
        assert deployment_call_args[0] == 'deployment'

    assert service_name == 'test-executor.test-ns.svc'


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
        ', "--host", "0.0.0.0", "--port-in",'
        ' "8081", "--port-out", "8082", "--port-ctrl", "8083"'
    )
    namespace = Namespace(**namespace)

    params = get_cli_params(namespace, skip_attr)

    assert params == expected_string + base_string


@pytest.mark.parametrize(
    ['dictionary', 'expected_string'],
    [
        ({'k1': 'v2', 'k2': 'v2'}, '{\\"k1\\": \\"v2\\", \\"k2\\": \\"v2\\"}'),
        ({'k1': 'v2', 'k2': ''}, '{\\"k1\\": \\"v2\\", \\"k2\\": \\"\\"}'),
        ({'k1': 'v2', 'k2': 3}, '{\\"k1\\": \\"v2\\", \\"k2\\": 3}'),
        (
            {'k1': 'v1', 'k2': {'k3': 'v3'}},
            '{\\"k1\\": \\"v1\\", \\"k2\\": {\\"k3\\": \\"v3\\"}}',
        ),
        (None, ''),
    ],
)
def test_dictionary_to_cli_param(dictionary: Dict, expected_string: str):
    assert dictionary_to_cli_param(dictionary) == expected_string


@pytest.mark.parametrize(
    'pod_args',
    [
        [
            '--k8s-uses-init',
            'test-image',
            '--k8s-init-container-command',
            'test-command',
            '--k8s-mount-path',
            'test/path',
        ],
        [
            '--k8s-init-container-command',
            'test-command',
            '--k8s-mount-path',
            'test/path',
        ],
        [],
    ],
)
def test_init_container_args(pod_args):
    args = set_pod_parser().parse_args(pod_args)
    pod = K8sPod(args)

    init_container = get_init_container_args(pod.args)

    if any(['--k8s-uses-init' in arg for arg in pod_args]):
        assert init_container == {
            'init-name': 'init',
            'init-image': args.k8s_uses_init,
            'init-command': f'{args.k8s_init_container_command}',
            'mount-path': args.k8s_mount_path,
        }
    else:
        assert init_container is None
