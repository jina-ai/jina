import json
from typing import Dict

import pytest

from jina.orchestrate.deployments.config.k8slib.kubernetes_tools import get_yaml


@pytest.mark.parametrize(
    ['template', 'params'],
    [
        ('namespace', {'name': 'test-ns'}),
        ('service', {'name': 'test-svc'}),
        ('deployment-executor', {'name': 'test-dep', 'protocol': 'grpc'}),
        (
            'configmap',
            {
                'name': 'test-configmap-executor',
                'namespace': 'test-configmap',
                'data': {'k1': 'v1', 'k2': 'v2'},
            },
        ),
    ],
)
def test_get(template: str, params: Dict):
    config = get_yaml(template=template, params=params)

    for v in params.values():
        if isinstance(v, str):
            assert v in json.dumps(config)
        elif isinstance(v, dict):
            for sub_key, sub_v in v.items():
                assert config['data'][sub_key] == sub_v


@pytest.mark.parametrize('template', ['deployment-executor'])
def test_get_deployment_with_device_plugin(template, monkeypatch):
    params = {
        'name': 'test-name',
        'namespace': 'test-namespace',
        'image': 'test-image',
        'replicas': 1,
        'command': 'test-command',
        'args': 'test-args',
        'protocol': 'grpc',
        'port': 1234,
        'port_out': 1234,
        'port_ctrl': 1234,
        'pull_policy': 1234,
        'device_plugins': {'hardware-vendor.example/foo': 2, 'nvidia.com/gpu:': 3},
    }

    config = get_yaml(template, params)

    assert config['spec']['template']['spec']['containers'][0]['resources'] == {
        'limits': {'hardware-vendor.example/foo': 2, 'nvidia.com/gpu:': 3}
    }
