from unittest.mock import Mock

import pytest

import jina
from jina.parsers import set_pod_parser
from jina.peapods.pods.k8s import K8sPod
from jina.peapods.pods.k8slib import kubernetes_tools
from jina.peapods.pods.k8slib.kubernetes_deployment import dictionary_to_cli_param


def test_dictionary_to_cli_param():
    assert (
        dictionary_to_cli_param({'k1': 'v1', 'k2': {'k3': 'v3'}})
        == '{\\"k1\\": \\"v1\\", \\"k2\\": {\\"k3\\": \\"v3\\"}}'
    )
