from typing import Union, Dict, Tuple
from unittest.mock import Mock

import pytest
from jinja2.utils import Namespace

import jina
from jina.parsers import set_pod_parser
from jina.peapods.pods.k8s import K8sPod
from jina.peapods.pods.k8slib import kubernetes_tools
from jina.peapods.pods.k8slib.kubernetes_deployment import dictionary_to_cli_param


@pytest.mark.parametrize('is_master', (True, False))
def test_version(is_master, requests_mock):
    args = set_pod_parser().parse_args(['--name', 'test-pod'])
    mock_create = Mock()
    kubernetes_tools.create = mock_create
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


def test_dictionary_to_cli_param():
    assert (
        dictionary_to_cli_param({'k1': 'v1', 'k2': {'k3': 'v3'}})
        == '{\\"k1\\": \\"v1\\", \\"k2\\": {\\"k3\\": \\"v3\\"}}'
    )


def test_parse_args_no_parallel():
    args = set_pod_parser().parse_args(['--parallel', '1'])
    pod = K8sPod(args)

    assert pod.deployment_args['head_deployment'] is None
    assert pod.deployment_args['tail_deployment'] is None
    assert pod.deployment_args['deployments'] == [args]


@pytest.mark.parametrize('parallel', [2, 3, 4, 5])
def test_parse_args_parallel(parallel):
    args = set_pod_parser().parse_args(['--parallel', str(parallel)])
    pod = K8sPod(args)

    assert pod.deployment_args['head_deployment'] == args
    assert pod.deployment_args['head_deployment'].uses == jina.__default_executor__
    assert pod.deployment_args['tail_deployment'] == args
    assert pod.deployment_args['tail_deployment'].uses == jina.__default_executor__
    assert pod.deployment_args['deployments'] == [args] * parallel


@pytest.mark.parametrize('parallel', [2, 3, 4, 5])
def test_parse_args_parallel_custom_exectuor(parallel):
    args = set_pod_parser().parse_args(
        [
            '--parallel',
            str(parallel),
            '--uses-before',
            'custom-executor',
            '--uses-after',
            'custom-executor',
        ]
    )
    pod = K8sPod(args)

    assert namespace_equal(
        args, pod.deployment_args['head_deployment'], skip_attr=('uses',)
    )
    assert pod.deployment_args['head_deployment'].uses == 'custom-executor'
    assert namespace_equal(
        args, pod.deployment_args['tail_deployment'], skip_attr=('uses',)
    )
    assert pod.deployment_args['tail_deployment'].uses == 'custom-executor'
    assert pod.deployment_args['deployments'] == [args] * parallel


def namespace_equal(
    n1: Union[Namespace, Dict], n2: Union[Namespace, Dict], skip_attr: Tuple = ()
) -> bool:
    """
    Checks that two `Namespace` object have equal public attributes.
    It skips attributes that start with a underscore and additional `skip_attr`.
    """
    for attr in filter(lambda x: x not in skip_attr and not x.startswith('_'), dir(n1)):
        if not getattr(n1, attr) == getattr(n2, attr):
            return False
    return True
