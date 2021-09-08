from typing import Dict
from unittest.mock import Mock
import os

import pytest
import kubernetes

from jina.peapods.pods.k8slib import kubernetes_tools


def test_lazy_load_k8s_client():
    kubernetes.config.load_kube_config = Mock()
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
def test_create(template: str, values: Dict):
    kubernetes.utils.create_from_yaml = Mock()

    # avoid deleting the config file so that we can check it
    os.remove = Mock()

    kubernetes_tools.create(template, values)

    # get the path to the config file
    path_to_config_file = os.remove.call_args[0][0]

    # get the content and check that the values are present
    with open(path_to_config_file, 'r') as fh:
        content = fh.read()
    for v in values.values():
        assert v in content

    os.unlink(path_to_config_file)
