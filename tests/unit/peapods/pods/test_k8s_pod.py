from unittest.mock import Mock

from jina.parsers import set_pod_parser
from jina.peapods.pods.k8s import K8sPod
from jina.peapods.pods.k8slib import kubernetes_tools


def test_pod_remote_pea_without_parallel():
    args = set_pod_parser().parse_args(['--name', 'test-pod', '--parallel', str(1)])
    mock_create = Mock()
    kubernetes_tools.create = mock_create
    pod = K8sPod(args)
    mock_request = Mock()
    import requests

    requests.get = mock_request
    with pod:
        assert (
            mock_create.call_count == 3
        )  # 3 because of namespace, service and deployment
        assert mock_request.call_count == 1
