from typing import Union, Dict, Tuple, List, Optional, Set
from unittest.mock import Mock

import pytest
from kubernetes import client

import jina
from jina.helper import Namespace
from jina.parsers import set_pod_parser, set_gateway_parser
from jina.peapods.pods.k8s import K8sPod
from jina.peapods.pods.k8slib import kubernetes_deployment, kubernetes_client
from jina.peapods.pods.k8slib.kubernetes_deployment import dictionary_to_cli_param


def namespace_equal(
    n1: Union[Namespace, Dict], n2: Union[Namespace, Dict], skip_attr: Tuple = ()
) -> bool:
    """
    Checks that two `Namespace` object have equal public attributes.
    It skips attributes that start with a underscore and additional `skip_attr`.
    """
    if n1 is None and n2 is None:
        return True
    for attr in filter(lambda x: x not in skip_attr and not x.startswith('_'), dir(n1)):
        if not getattr(n1, attr) == getattr(n2, attr):
            return False
    return True


@pytest.mark.parametrize('is_master', (True, False))
def test_version(is_master, requests_mock):
    args = set_pod_parser().parse_args(['--name', 'test-pod'])
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
    if is_master:
        assert pod.version == 'master'
    else:
        assert pod.version == jina.__version__


def test_dictionary_to_cli_param():
    assert (
        dictionary_to_cli_param({'k1': 'v1', 'k2': {'k3': 'v3'}})
        == '{\\"k1\\": \\"v1\\", \\"k2\\": {\\"k3\\": \\"v3\\"}}'
    )


@pytest.mark.parametrize('shards', [1, 2, 3, 4, 5])
def test_parse_args(shards: int):
    args = set_pod_parser().parse_args(['--shards', str(shards)])
    pod = K8sPod(args)

    assert namespace_equal(
        pod.deployment_args['head_deployment'], None if shards == 1 else args
    )
    assert namespace_equal(
        pod.deployment_args['tail_deployment'], None if shards == 1 else args
    )
    for i, depl_arg in enumerate(pod.deployment_args['deployments']):
        import copy

        cargs = copy.deepcopy(args)
        cargs.shard_id = i
        assert depl_arg == cargs


@pytest.mark.parametrize('shards', [2, 3, 4, 5])
def test_parse_args_custom_executor(shards: int):
    uses_before = 'custom-executor-before'
    uses_after = 'custom-executor-after'
    args = set_pod_parser().parse_args(
        [
            '--shards',
            str(shards),
            '--uses-before',
            uses_before,
            '--uses-after',
            uses_after,
        ]
    )
    pod = K8sPod(args)

    assert namespace_equal(
        args, pod.deployment_args['head_deployment'], skip_attr=('uses',)
    )
    assert pod.deployment_args['head_deployment'].uses == uses_before
    assert namespace_equal(
        args, pod.deployment_args['tail_deployment'], skip_attr=('uses',)
    )
    assert pod.deployment_args['tail_deployment'].uses == uses_after
    for i, depl_arg in enumerate(pod.deployment_args['deployments']):
        import copy

        cargs = copy.deepcopy(args)
        cargs.shard_id = i
        assert depl_arg == cargs


@pytest.mark.parametrize(
    ['name', 'shards', 'expected_deployments'],
    [
        (
            'gateway',
            '1',
            [{'name': 'gateway', 'head_host': 'gateway.ns.svc'}],
        ),
        (
            'test-pod',
            '1',
            [{'name': 'test-pod', 'head_host': 'test-pod.ns.svc'}],
        ),
        (
            'test-pod',
            '2',
            [
                {
                    'name': 'test-pod-head',
                    'head_host': 'test-pod-head.ns.svc',
                },
                {'name': 'test-pod-0', 'head_host': 'test-pod-0.ns.svc'},
                {'name': 'test-pod-1', 'head_host': 'test-pod-1.ns.svc'},
                {
                    'name': 'test-pod-tail',
                    'head_host': 'test-pod-tail.ns.svc',
                },
            ],
        ),
    ],
)
def test_deployments(name: str, shards: str, expected_deployments: List[Dict]):
    args = set_pod_parser().parse_args(
        ['--name', name, '--shards', shards, '--k8s-namespace', 'ns']
    )
    pod = K8sPod(args)

    actual_deployments = pod.deployments

    assert len(actual_deployments) == len(expected_deployments)

    for actual, expected in zip(actual_deployments, expected_deployments):
        assert actual['name'] == expected['name']
        assert actual['head_host'] == expected['head_host']
        assert actual['head_port_in'] == pod.fixed_head_port_in
        assert actual['tail_port_out'] == pod.fixed_tail_port_out
        assert actual['head_zmq_identity'] == pod.head_zmq_identity


def get_k8s_pod(
    pod_name: str,
    namespace: str,
    shards: str = None,
    replicas: str = None,
    needs: Optional[Set[str]] = None,
    uses_before=None,
    uses_after=None,
    port_expose=None,
):
    parameter_list = ['--name', pod_name, '--k8s-namespace', namespace]
    if shards:
        parameter_list.extend(
            [
                '--shards',
                str(shards),
            ]
        )
    if replicas:
        parameter_list.extend(
            [
                '--replicas',
                str(replicas),
            ]
        )

    if port_expose:
        parameter_list.extend(
            [
                '--port-expose',
                str(port_expose),
            ]
        )
    if uses_before:
        parameter_list.extend(
            [
                '--uses-before',
                uses_before,
            ]
        )
    if uses_after:
        parameter_list.extend(['--uses-after', uses_after])
    parameter_list.append('--noblock-on-start')
    parser = set_gateway_parser() if pod_name == 'gateway' else set_pod_parser()
    args = parser.parse_args(parameter_list)
    pod = K8sPod(args, needs)
    return pod


def test_start_creates_namespace():
    ns = 'test'
    pod = get_k8s_pod('gateway', ns, port_expose=8085)
    kubernetes_deployment.deploy_service = Mock()
    pod.start()
    assert kubernetes_deployment.deploy_service.call_args[0][0] == 'gateway'
    assert kubernetes_deployment.deploy_service.call_args[1]['port_expose'] == 8085


def test_start_deploys_gateway():
    pod_name = 'gateway'
    ns = 'test-flow'

    kubernetes_deployment.deploy_service = Mock()
    kubernetes_deployment.get_cli_params = Mock()

    pod = get_k8s_pod(pod_name, ns)
    pod.start()

    kubernetes_deployment.deploy_service.assert_called_once()

    assert kubernetes_deployment.deploy_service.call_args[0][0] == pod_name
    call_kwargs = kubernetes_deployment.deploy_service.call_args[1]
    assert call_kwargs['namespace'] == ns
    assert pod.version in call_kwargs['image_name']

    kubernetes_deployment.get_cli_params.assert_called_once()
    assert kubernetes_deployment.get_cli_params.call_args[0][0] == pod.args
    assert kubernetes_deployment.get_cli_params.call_args[0][1] == ('pod_role',)


def test_start_deploys_runtime():
    pod_name = 'executor'
    namespace = 'ns'
    pod = get_k8s_pod(pod_name, namespace)

    assert len(pod.k8s_deployments) > 0
    for deployment in pod.k8s_deployments:
        deployment._construct_runtime_container_args = Mock()
    kubernetes_deployment.deploy_service = Mock()

    pod.start()

    kubernetes_deployment.deploy_service.assert_called_once()
    dns_name = kubernetes_deployment.deploy_service.call_args[0][0]
    kwargs = kubernetes_deployment.deploy_service.call_args[1]

    assert dns_name == pod_name
    assert kwargs['namespace'] == namespace
    assert kwargs['image_name'] == f'jinaai/jina:{pod.version}-py38-perf'
    assert kwargs['replicas'] == 1
    assert kwargs['init_container'] is None
    assert kwargs['custom_resource_dir'] is None

    assert len(pod.k8s_deployments) > 0
    for i, deployment in enumerate(pod.k8s_deployments):
        deployment._construct_runtime_container_args.assert_called_once()
        call_args = deployment._construct_runtime_container_args.call_args[0]
        assert call_args[0] == deployment.deployment_args
        assert call_args[1] == pod.args.uses
        assert call_args[2] == kubernetes_deployment.dictionary_to_cli_param(
            {'pea_id': i}
        )
        assert call_args[3] == ''


@pytest.mark.parametrize('shards', [2, 3, 4])
def test_start_deploys_runtime_with_shards(shards: int):
    namespace = 'ns'
    pod = get_k8s_pod('executor', namespace, str(shards))

    deploy_mock = Mock()
    kubernetes_deployment.deploy_service = deploy_mock

    pod.start()

    expected_calls = shards + 2  # for head and tail

    assert expected_calls == kubernetes_deployment.deploy_service.call_count

    head_call_args = deploy_mock.call_args_list[0][0]
    assert head_call_args[0] == pod.name + '-head'

    executor_call_args_list = [
        deploy_mock.call_args_list[i][0] for i in range(1, shards + 1)
    ]
    for i, call_args in enumerate(executor_call_args_list):
        assert call_args[0] == pod.name + f'-{i}'

    tail_call_args = deploy_mock.call_args_list[-1][0]
    assert tail_call_args[0] == pod.name + '-tail'


@pytest.mark.parametrize(
    'needs, replicas, expected_calls, expected_executors',
    [
        (None, 1, 1, ['executor']),
        (None, 2, 1, ['executor']),
        (['first_pod'], 1, 1, ['executor']),
        (['first_pod'], 2, 1, ['executor']),
        (['first_pod', 'second_pod'], 1, 1, ['executor']),
        (['first_pod', 'second_pod'], 2, 2, ['executor-head', 'executor']),
        (['first_pod', 'second_pod', 'third_pod'], 1, 1, ['executor']),
        (['first_pod', 'second_pod', 'third_pod'], 2, 2, ['executor-head', 'executor']),
    ],
)
def test_needs(needs, replicas, expected_calls, expected_executors):
    namespace = 'ns'
    pod = get_k8s_pod('executor', namespace, str(1), str(replicas), needs)

    deploy_mock = Mock()
    kubernetes_deployment.deploy_service = deploy_mock
    pod.start()
    assert expected_calls == kubernetes_deployment.deploy_service.call_count

    actual_executors = [executor[0][0] for executor in deploy_mock.call_args_list]
    assert actual_executors == expected_executors


@pytest.mark.parametrize(
    'uses_before, uses_after, expected_calls, expected_executors',
    [
        (None, None, 1, ['executor']),
        ('custom_head', None, 2, ['executor-head', 'executor']),
        (None, 'custom_tail', 2, ['executor', 'executor-tail']),
        (
            'custom_head',
            'custom_tail',
            3,
            ['executor-head', 'executor', 'executor-tail'],
        ),
    ],
)
def test_uses_before_and_uses_after(
    uses_before, uses_after, expected_calls, expected_executors
):
    namespace = 'ns'
    pod = get_k8s_pod(
        'executor', namespace, str(1), uses_before=uses_before, uses_after=uses_after
    )
    deploy_mock = Mock()
    kubernetes_deployment.deploy_service = deploy_mock
    pod.start()
    assert expected_calls == kubernetes_deployment.deploy_service.call_count

    actual_executors = [executor[0][0] for executor in deploy_mock.call_args_list]
    assert actual_executors == expected_executors


@pytest.mark.parametrize(
    'name, k8s_namespace, shards, replicas, needs, uses_before',
    [
        (
            'test-with-multiple-shards',
            'test-namespace',
            '2',
            '1',
            [],
            False,
        ),  # shards > 1
        (
            'test-with-replicas-needs',
            'test-namespace',
            '1',
            '2',
            [1, 2],
            False,
        ),  # replicas > 1 and needs
        ('test-with-uses-before', 'test-namespace', '1', '1', [], True),  # uses before
    ],
)
def test_pod_start_close_given_head_deployment(
    name, k8s_namespace, shards, replicas, mocker, needs, uses_before
):
    args_list = [
        '--name',
        name,
        '--k8s-namespace',
        k8s_namespace,
        '--shards',
        shards,
        '--replicas',
        replicas,
        '--noblock-on-start',
    ]
    if uses_before:
        args_list.extend(['--uses-before', 'custom-executor-before'])
    args = set_pod_parser().parse_args(args_list)
    mocker.patch(
        'jina.peapods.pods.k8slib.kubernetes_deployment.deploy_service',
        return_value=f'{name}.{k8s_namespace}.svc',
    )
    mocker.patch(
        'jina.peapods.pods.k8s.K8sPod._K8sDeployment._delete_namespaced_deployment',
        return_value=client.V1Status(status=200),
    )
    with K8sPod(args, needs=needs) as pod:
        # enter `_deploy_runtime`
        assert isinstance(pod.k8s_head_deployment, K8sPod._K8sDeployment)
        assert pod.k8s_head_deployment.name == name + '-head'
        assert pod.args.noblock_on_start


@pytest.mark.parametrize(
    'name, k8s_namespace, shards, uses_after',
    [
        (
            'test-with-multiple-shards',
            'test-namespace',
            '2',
            False,
        ),  # shards > 1
        (
            'test-with-uses-after',
            'test-namespace',
            '1',
            True,
        ),  # uses-after
    ],
)
def test_pod_start_close_given_tail_deployment(
    name, k8s_namespace, shards, mocker, uses_after
):
    args_list = [
        '--name',
        name,
        '--k8s-namespace',
        k8s_namespace,
        '--shards',
        shards,
        '--noblock-on-start',
    ]
    if uses_after:
        args_list.extend(['--uses-after', 'custom-executor-after'])
    args = set_pod_parser().parse_args(args_list)
    mocker.patch(
        'jina.peapods.pods.k8slib.kubernetes_deployment.deploy_service',
        return_value=f'{name}.{k8s_namespace}.svc',
    )
    mocker.patch(
        'jina.peapods.pods.k8s.K8sPod._K8sDeployment._delete_namespaced_deployment',
        return_value=client.V1Status(status=200),
    )
    with K8sPod(args) as pod:
        # enter `_deploy_runtime`
        assert isinstance(pod.k8s_tail_deployment, K8sPod._K8sDeployment)
        assert pod.k8s_tail_deployment.name == name + '-tail'
        assert pod.args.noblock_on_start


@pytest.mark.parametrize(
    'all_replicas_ready',
    [
        True,  # enter wait-until-success and ready replicas = num of replicas
        False,  # enter wait-until-success and ready replicas < num of replicas
    ],
)
def test_pod_wait_for_success(all_replicas_ready, mocker, caplog):
    args_list = [
        '--name',
        'test-wait-success',
        '--k8s-namespace',
        'test-namespace',
        '--shards',
        '1',
        '--replicas',
        '3',
        '--timeout-ready',
        '100',
    ]
    if all_replicas_ready:
        mocker.patch(
            'jina.peapods.pods.k8s.K8sPod._K8sDeployment._read_namespaced_deployment',
            return_value=client.V1Deployment(
                status=client.V1DeploymentStatus(replicas=3, ready_replicas=3)
            ),
        )  # all ready
    else:
        mocker.patch(
            'jina.peapods.pods.k8s.K8sPod._K8sDeployment._read_namespaced_deployment',
            return_value=client.V1Deployment(
                status=client.V1DeploymentStatus(replicas=3, ready_replicas=1)
            ),
        )  # not all peas ready
    args = set_pod_parser().parse_args(args_list)
    mocker.patch(
        'jina.peapods.pods.k8slib.kubernetes_deployment.deploy_service',
        return_value=f'test-wait-success.test-namespace.svc',
    )
    mocker.patch(
        'jina.peapods.pods.k8s.K8sPod._K8sDeployment._delete_namespaced_deployment',
        return_value=client.V1Status(status=200),
    )
    if all_replicas_ready:
        with K8sPod(args):
            pass
    else:
        # expect Number of ready replicas 1, waiting for 2 replicas to be available
        # keep waiting, and we set a small timeout-ready, raise the exception
        with pytest.raises(jina.excepts.RuntimeFailToStart):
            with K8sPod(args):
                pass


def test_pod_with_gpus(mocker):
    args_list = [
        '--name',
        'test-wait-success',
        '--k8s-namespace',
        'test-namespace',
        '--shards',
        '1',
        '--replicas',
        '1',
        '--gpus',
        '3',
    ]
    args = set_pod_parser().parse_args(args_list)
    container = client.V1Container(
        name='test-container',
        resources=client.V1ResourceRequirements(limits={'nvidia.com/gpu': 3}),
    )
    spec = client.V1PodSpec(containers=[container])
    mocker.patch(
        'jina.peapods.pods.k8s.K8sPod._K8sDeployment._read_namespaced_deployment',
        return_value=client.V1Deployment(
            status=client.V1DeploymentStatus(replicas=1, ready_replicas=1), spec=spec
        ),
    )
    mocker.patch(
        'jina.peapods.pods.k8slib.kubernetes_deployment.deploy_service',
        return_value=f'test-wait-success.test-namespace.svc',
    )
    mocker.patch(
        'jina.peapods.pods.k8s.K8sPod._K8sDeployment._delete_namespaced_deployment',
        return_value=client.V1Status(status=200),
    )
    with K8sPod(args) as pod:
        assert pod.args.gpus == '3'
