import pytest

from jina.peapods.pods.k8slib.kubernetes_client import K8sClients


@pytest.fixture
def k8s_clients(mocker):
    mocker.patch('kubernetes.config.load_kube_config', return_value=None)
    return K8sClients()


def test_init(k8s_clients):
    assert k8s_clients._k8s_client
    assert not k8s_clients._apps_v1
    assert not k8s_clients._core_v1
    assert not k8s_clients._beta
    assert not k8s_clients._networking_v1_beta1_api


def test_k8s_client(k8s_clients):
    assert k8s_clients.k8s_client


def test_apps_v1(k8s_clients):
    assert k8s_clients.apps_v1


def test_core_v1(k8s_clients):
    assert k8s_clients.core_v1


def test_beta(k8s_clients):
    assert k8s_clients.beta


def test_networking_v1_beta1_api(k8s_clients):
    assert k8s_clients.networking_v1_beta1_api
