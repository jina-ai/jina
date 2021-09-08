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
    ['template', 'values'],
    [
        ('namespace', {'name': 'test-ns'}),
        ('service', {'name': 'test-svc'}),
        ('deployment', {'name': 'test-dep'}),
        ('deployment-init', {'name': 'test-dep-init'}),
    ],
)
def test_create(template: str, values: Dict, monkeypatch):
    create_from_yaml_mock = Mock()
    monkeypatch.setattr(kubernetes.utils, 'create_from_yaml', create_from_yaml_mock)

    # avoid deleting the config file so that we can check it
    remove_mock = Mock()
    monkeypatch.setattr(os, 'remove', remove_mock)

    create(template, values)

    # get the path to the config file
    assert remove_mock.call_count == 1
    path_to_config_file = remove_mock.call_args[0][0]

    # get the content and check that the values are present
    with open(path_to_config_file, 'r') as fh:
        content = fh.read()
    for v in values.values():
        assert v in content

    monkeypatch.undo()
    os.remove(path_to_config_file)
