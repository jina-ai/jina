from unittest.mock import Mock

import pytest

import jina
from jina.parsers import set_pod_parser
from jina.peapods.pods.k8s import K8sPod
from jina.peapods.pods.k8slib import kubernetes_tools
from jina.peapods.pods.k8slib.kubernetes_deployment import dictionary_to_cli_param


@pytest.mark.parametrize('is_master', (True, False))
def test_version(is_master, requests_mock, monkeypatch):
    args = set_pod_parser().parse_args(['--name', 'test-pod'])
    mock_create = Mock()
    monkeypatch.setattr(kubernetes_tools, 'create', mock_create)
    if is_master:
        version = 'v2'
    else:
        # current version is published already
        version = jina.__version__
    requests_mock.get(
        'https://registry.hub.docker.com/v1/repositories/jinaai/jina/tags',
        text='[{"name": "v1"}, {"name": "' + version + '"}]',
    )
    pod = K8sPod(args)

    with pod:
        assert (
            mock_create.call_count == 3
        )  # 3 because of namespace, service and deployment
        if is_master:
            assert pod.version == 'master'
        else:
            assert pod.version == jina.__version__
