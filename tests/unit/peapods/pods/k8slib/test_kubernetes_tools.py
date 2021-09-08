from typing import Dict
from unittest.mock import Mock

import pytest
import kubernetes

from jina.peapods.pods.k8slib import kubernetes_tools
from jina.peapods.pods.k8slib.kubernetes_tools import os


def test_lazy_load_k8s_client(monkeypatch):
    load_kube_config_mock = Mock()
    monkeypatch.setattr(kubernetes.config, 'load_kube_config', load_kube_config_mock)
    attributes = ['k8s_client', 'v1', 'beta', 'networking_v1_beta1_api']
    for attribute in attributes:
        assert (
            getattr(kubernetes_tools.__k8s_clients, f'_K8SClients__{attribute}') is None
        )

    for attribute in attributes:
        assert getattr(kubernetes_tools.__k8s_clients, attribute) is not None


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
    os.remove = Mock()

    kubernetes_tools.create(template, values)
    print(kubernetes_tools.create)

    # get the path to the config file
    assert os.remove.call_count == 1
    path_to_config_file = os.remove.call_args[0][0]

    # get the content and check that the values are present
    with open(path_to_config_file, 'r') as fh:
        content = fh.read()
    for v in values.values():
        assert v in content

    os.unlink(path_to_config_file)
