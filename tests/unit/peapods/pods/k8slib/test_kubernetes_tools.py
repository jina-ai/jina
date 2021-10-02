import json
from typing import Dict
from unittest.mock import Mock

import os
import pytest
import kubernetes

from jina.peapods.pods.k8slib.kubernetes_tools import create
from jina.peapods.pods.k8slib.kubernetes_tools import __k8s_clients


def test_lazy_load_k8s_client(monkeypatch):
    load_kube_config_mock = Mock()
    monkeypatch.setattr(kubernetes.config, 'load_kube_config', load_kube_config_mock)
    attributes = ['k8s_client', 'v1', 'beta', 'networking_v1_beta1_api']
    for attribute in attributes:
        assert getattr(__k8s_clients, f'_K8SClients__{attribute}') is None

    for attribute in attributes:
        assert getattr(__k8s_clients, attribute) is not None


@pytest.mark.parametrize(
    ['template', 'kind', 'params'],
    [
        ('namespace', 'Namespace', {'name': 'test-ns'}),
        ('service', 'Service', {'name': 'test-svc'}),
        ('deployment', 'Deployment', {'name': 'test-dep'}),
        ('deployment-init', 'Deployment', {'name': 'test-dep-init'}),
        (
            'configmap',
            'ConfigMap',
            {'namespace': 'test-configmap', 'data': {'k1': 'v1', 'k2': 'v2'}},
        ),
    ],
)
def test_create(template: str, kind: str, params: Dict, monkeypatch):
    create_from_yaml_mock = Mock()
    monkeypatch.setattr(kubernetes.utils, 'create_from_yaml', create_from_yaml_mock)

    # avoid deleting the config file so that we can check it
    remove_mock = Mock()
    monkeypatch.setattr(os, 'remove', remove_mock)

    create(template=template, kind=kind, params=params)

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
