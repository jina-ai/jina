import os
import json
from typing import Dict
from unittest.mock import Mock

import yaml
import pytest
import kubernetes

from jina.peapods.pods.k8slib.kubernetes_tools import create
from jina.peapods.pods.k8slib.kubernetes_client import K8sClients


def test_lazy_load_k8s_client(monkeypatch):
    load_kube_config_mock = Mock()
    monkeypatch.setattr(kubernetes.config, 'load_kube_config', load_kube_config_mock)
    k8s_clients = K8sClients()
    attributes = ['core_v1', 'beta', 'networking_v1_beta1_api', 'apps_v1']
    for attribute in attributes:
        assert getattr(k8s_clients, f'_{attribute}') is None

    for attribute in attributes:
        assert getattr(k8s_clients, attribute) is not None


@pytest.mark.parametrize(
    ['template', 'params'],
    [
        ('namespace', {'name': 'test-ns'}),
        ('service', {'name': 'test-svc'}),
        ('deployment', {'name': 'test-dep'}),
        ('deployment-init', {'name': 'test-dep-init'}),
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
def test_create(template: str, params: Dict, monkeypatch):
    create_from_yaml_mock = Mock()
    load_kube_config_mock = Mock()
    monkeypatch.setattr(kubernetes.utils, 'create_from_yaml', create_from_yaml_mock)
    monkeypatch.setattr(kubernetes.config, 'load_kube_config', load_kube_config_mock)

    # avoid deleting the config file so that we can check it
    remove_mock = Mock()
    monkeypatch.setattr(os, 'remove', remove_mock)

    create(template=template, params=params)

    # get the path to the config file
    assert remove_mock.call_count == 1
    path_to_config_file = remove_mock.call_args[0][0]

    # get the content and check that the values are present
    with open(path_to_config_file, 'r') as fh:
        content = fh.read()
    for v in params.values():
        if isinstance(v, str):
            assert v in content
        elif isinstance(v, dict):
            dict_content = json.loads(content)
            for sub_key, sub_v in v.items():
                assert dict_content['data'][sub_key] == sub_v

    monkeypatch.undo()
    os.remove(path_to_config_file)


@pytest.mark.parametrize('template', ['deployment', 'deployment-init'])
def test_create_deployment_with_device_plugin(template, monkeypatch):
    params = {
        'name': 'test-name',
        'namespace': 'test-namespace',
        'image': 'test-image',
        'replicas': 1,
        'command': 'test-command',
        'args': 'test-args',
        'port_expose': 1234,
        'port_in': 1234,
        'port_out': 1234,
        'port_ctrl': 1234,
        'pull_policy': 1234,
        'device_plugins': {'hardware-vendor.example/foo': 2, 'nvidia.com/gpu:': 3},
    }

    create_from_yaml_mock = Mock()
    load_kube_config_mock = Mock()
    remove_mock = Mock()
    monkeypatch.setattr(kubernetes.utils, 'create_from_yaml', create_from_yaml_mock)
    monkeypatch.setattr(kubernetes.config, 'load_kube_config', load_kube_config_mock)
    monkeypatch.setattr(os, 'remove', remove_mock)

    create(template, params)

    assert remove_mock.call_count == 1
    path_to_config_file = remove_mock.call_args[0][0]

    with open(path_to_config_file, 'r') as f:
        config = yaml.safe_load(f)
        assert config['spec']['template']['spec']['containers'][0]['resources'] == {
            'limits': {'hardware-vendor.example/foo': 2, 'nvidia.com/gpu:': 3}
        }
