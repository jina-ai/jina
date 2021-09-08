from unittest.mock import Mock
import os

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


def test_create():
    kubernetes.utils.create_from_yaml = Mock()
    os.remove = Mock()
    ns = 'test_namespace_name'

    kubernetes_tools.create('namespace', {'name': ns})

    path = kubernetes.utils.create_from_yaml.call_args[0][1]
    assert (
        kubernetes.utils.create_from_yaml.call_args[0][0]
        == kubernetes_tools.__k8s_clients.k8s_client
    )

    with open(path, 'r') as fh:
        content = fh.read()
    assert ns in content

    os.unlink(path)
