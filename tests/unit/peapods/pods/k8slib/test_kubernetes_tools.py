import json
from typing import Dict
from unittest.mock import Mock

import os
import pytest
import kubernetes

from jina.peapods.pods.k8slib.kubernetes_tools import create
from jina.peapods.pods.k8slib.kubernetes_client import K8sClients


def test_lazy_load_k8s_client(monkeypatch):
    load_kube_config_mock = Mock()
    k8s_clients = K8sClients()
    monkeypatch.setattr(kubernetes.config, 'load_kube_config', load_kube_config_mock)
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
