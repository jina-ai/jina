from typing import Union, Dict, Tuple, List, Optional, Set
from unittest.mock import Mock
import json
import pytest
from kubernetes import client

from jina import __version__, __default_executor__
from jina.helper import Namespace
from jina.parsers import set_pod_parser, set_gateway_parser
from jina.peapods.networking import K8sGrpcConnectionPool
from jina.peapods.pods.config.k8s import _get_base_executor_version, K8sPodConfig
from jina.peapods.pods.config.k8slib import kubernetes_deployment


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
            print(f' differ in {attr} => {getattr(n1, attr)} vs {getattr(n2, attr)}')
            return False
    return True


@pytest.mark.parametrize('is_master', (True, False))
def test_version(is_master, requests_mock):
    if is_master:
        version = 'v2'
    else:
        # current version is published already
        version = __version__
    requests_mock.get(
        'https://registry.hub.docker.com/v1/repositories/jinaai/jina/tags',
        text='[{"name": "v1"}, {"name": "' + version + '"}]',
    )
    v = _get_base_executor_version()
    if is_master:
        assert v == 'master'
    else:
        assert v == __version__


@pytest.mark.parametrize('shards', [1, 2, 3, 4, 5])
@pytest.mark.parametrize('k8s_connection_pool_call', [False, True])
def test_parse_args(shards: int, k8s_connection_pool_call: bool):
    args = set_pod_parser().parse_args(['--shards', str(shards), '--name', 'executor'])
    pod_config = K8sPodConfig(args, 'default-namespace', k8s_connection_pool_call)

    assert namespace_equal(
        pod_config.deployment_args['head_deployment'],
        args,
        skip_attr=(
            'runtime_cls',
            'pea_role',
            'port_in',
            'k8s_namespace',
            'k8s_connection_pool',
            'name',
            'uses',
            'connection_list',
        ),
    )
    assert (
        pod_config.deployment_args['head_deployment'].k8s_namespace
        == 'default-namespace'
    )
    assert pod_config.deployment_args['head_deployment'].name == 'executor/head-0'
    assert pod_config.deployment_args['head_deployment'].runtime_cls == 'HeadRuntime'
    assert pod_config.deployment_args['head_deployment'].uses is None
    assert pod_config.deployment_args['head_deployment'].uses_before is None
    assert pod_config.deployment_args['head_deployment'].uses_after is None
    assert (
        pod_config.deployment_args['head_deployment'].k8s_connection_pool
        is k8s_connection_pool_call
    )
    assert pod_config.deployment_args['head_deployment'].uses_before_address is None
    assert pod_config.deployment_args['head_deployment'].uses_after_address is None
    if k8s_connection_pool_call:
        assert pod_config.deployment_args['head_deployment'].connection_list is None
    else:
        if shards > 1:
            candidate_connection_list = {
                str(i): f'executor-{i}.default-namespace.svc:8081'
                for i in range(shards)
            }
        else:
            candidate_connection_list = {'0': f'executor.default-namespace.svc:8081'}
        assert pod_config.deployment_args[
            'head_deployment'
        ].connection_list == json.dumps(candidate_connection_list)
    for i, depl_arg in enumerate(pod_config.deployment_args['deployments']):
        import copy

        cargs = copy.deepcopy(args)
        cargs.shard_id = i
        assert depl_arg.k8s_connection_pool is False
        assert namespace_equal(
            depl_arg,
            cargs,
            skip_attr=(
                'runtime_cls',
                'pea_role',
                'port_in',
                'k8s_namespace',
                'k8s_connection_pool',
            ),
        )


@pytest.mark.parametrize('shards', [2, 3, 4, 5])
@pytest.mark.parametrize('k8s_connection_pool_call', [False, True])
def test_parse_args_custom_executor(shards: int, k8s_connection_pool_call: bool):
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
    pod_config = K8sPodConfig(args, 'default-namespace', k8s_connection_pool_call)

    assert pod_config.deployment_args['head_deployment'].runtime_cls == 'HeadRuntime'
    assert pod_config.deployment_args['head_deployment'].uses_before == uses_before
    assert (
        pod_config.deployment_args['head_deployment'].uses_before_address
        == f'127.0.0.1:8082'
    )
    assert pod_config.deployment_args['head_deployment'].uses is None
    assert pod_config.deployment_args['head_deployment'].uses_after == uses_after
    assert (
        pod_config.deployment_args['head_deployment'].uses_after_address
        == f'127.0.0.1:8083'
    )
    assert (
        pod_config.deployment_args['head_deployment'].k8s_connection_pool
        is k8s_connection_pool_call
    )
    assert (
        pod_config.deployment_args['head_deployment'].uses_before_address
        == f'127.0.0.1:{K8sGrpcConnectionPool.K8S_PORT_USES_BEFORE}'
    )
    assert (
        pod_config.deployment_args['head_deployment'].uses_after_address
        == f'127.0.0.1:{K8sGrpcConnectionPool.K8S_PORT_USES_AFTER}'
    )

    for i, depl_arg in enumerate(pod_config.deployment_args['deployments']):
        import copy

        cargs = copy.deepcopy(args)
        cargs.shard_id = i
        assert depl_arg.k8s_connection_pool is False
        assert namespace_equal(
            depl_arg,
            cargs,
            skip_attr=(
                'uses_before',
                'uses_after',
                'port_in',
                'k8s_namespace',
                'k8s_connection_pool',
            ),
        )


@pytest.mark.parametrize(
    ['name', 'shards'],
    [
        (
            'gateway',
            '1',
        ),
        (
            'test-pod',
            '1',
        ),
        (
            'test-pod',
            '2',
        ),
    ],
)
@pytest.mark.parametrize('k8s_connection_pool_call', [False, True])
def test_deployments(name: str, shards: str, k8s_connection_pool_call):
    args = set_pod_parser().parse_args(['--name', name, '--shards', shards])
    pod_config = K8sPodConfig(args, 'ns', k8s_connection_pool_call)

    actual_deployments = pod_config.worker_deployments

    assert len(actual_deployments) == int(shards)
    for i, deploy in enumerate(actual_deployments):
        if int(shards) > 1:
            assert deploy.name == f'{name}-{i}'
        else:
            assert deploy.name == name
        assert deploy.head_port_in == K8sGrpcConnectionPool.K8S_PORT_IN
        assert deploy.jina_pod_name == name
        assert deploy.shard_id == i
        assert deploy.k8s_connection_pool is k8s_connection_pool_call


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
    _mock_delete(pod)

    with pod:
        assert kubernetes_deployment.deploy_service.call_args[0][0] == 'gateway'
        assert kubernetes_deployment.deploy_service.call_args[1]['port_expose'] == 8085


def _mock_delete(pod):
    mock = Mock()
    mock.status = 'Success'
    for d in pod.k8s_deployments:
        d._delete_namespaced_deployment = lambda *args, **kwargs: mock
    if pod.k8s_head_deployment:
        pod.k8s_head_deployment._delete_namespaced_deployment = (
            lambda *args, **kwargs: mock
        )


def test_start_deploys_gateway():
    pod_name = 'gateway'
    ns = 'test-flow'

    kubernetes_deployment.deploy_service = Mock()
    kubernetes_deployment.get_cli_params = Mock()

    pod = get_k8s_pod(pod_name, ns)
    _mock_delete(pod)

    with pod:
        kubernetes_deployment.deploy_service.assert_called_once()

        assert kubernetes_deployment.deploy_service.call_args[0][0] == pod_name
        call_kwargs = kubernetes_deployment.deploy_service.call_args[1]
        assert call_kwargs['namespace'] == ns
        assert pod.version in call_kwargs['image_name']

        kubernetes_deployment.get_cli_params.assert_called_once()


@pytest.mark.parametrize(
    'uses_before, uses_after',
    [
        (None, None),
        ('uses_before_exec', None),
        (None, 'uses_after_exec'),
        ('uses_before_exec', 'uses_after_exec'),
    ],
)
def test_start_deploys_runtime(uses_before, uses_after):
    pod_name = 'executor'
    namespace = 'ns'
    pod = get_k8s_pod(
        pod_name, namespace, uses_before=uses_before, uses_after=uses_after
    )
    _mock_delete(pod)

    assert len(pod.k8s_deployments) > 0
    for deployment in pod.k8s_deployments:
        deployment._construct_runtime_container_args = Mock()
    pod.k8s_head_deployment._construct_runtime_container_args = Mock()
    kubernetes_deployment.deploy_service = Mock()

    with pod:
        assert 2 == kubernetes_deployment.deploy_service.call_count
        dns_name = kubernetes_deployment.deploy_service.call_args[0][0]
        kwargs = kubernetes_deployment.deploy_service.call_args[1]

        assert dns_name == pod_name
        assert kwargs['namespace'] == namespace
        assert kwargs['image_name'] == f'jinaai/jina:{pod.version}-py38-perf'
        assert kwargs['replicas'] == 1
        assert kwargs['init_container'] is None
        assert kwargs['custom_resource_dir'] is None

        assert len(pod.k8s_deployments) == 1
        assert pod.k8s_head_deployment.head_port_in == 8081


@pytest.mark.parametrize('shards', [2, 3, 4])
def test_start_deploys_runtime_with_shards(shards: int):
    namespace = 'ns'
    pod = get_k8s_pod('executor', namespace, str(shards))

    deploy_mock = Mock()
    kubernetes_deployment.deploy_service = deploy_mock

    pod.start()

    expected_calls = shards + 1  # for head

    assert expected_calls == kubernetes_deployment.deploy_service.call_count

    head_call_args = deploy_mock.call_args_list[0][0]
    assert head_call_args[0] == pod.name + '-head'

    executor_call_args_list = [
        deploy_mock.call_args_list[i][0] for i in range(1, shards + 1)
    ]
    for i, call_args in enumerate(executor_call_args_list):
        assert call_args[0] == pod.name + f'-{i}'


@pytest.mark.parametrize(
    'needs, replicas, expected_calls, expected_executors',
    [
        (None, 1, 2, ['executor-head', 'executor']),
        (None, 2, 2, ['executor-head', 'executor']),
        (['first_pod'], 1, 2, ['executor-head', 'executor']),
        (['first_pod'], 2, 2, ['executor-head', 'executor']),
        (['first_pod', 'second_pod'], 1, 2, ['executor-head', 'executor']),
        (['first_pod', 'second_pod'], 2, 2, ['executor-head', 'executor']),
        (['first_pod', 'second_pod', 'third_pod'], 1, 2, ['executor-head', 'executor']),
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
        (None, None, 2, ['executor-head', 'executor']),
        ('custom_head', None, 2, ['executor-head', 'executor']),
        (None, 'custom_tail', 2, ['executor-head', 'executor']),
        (
            'custom_head',
            'custom_tail',
            2,
            ['executor-head', 'executor'],
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
        pod = K8sPod(args)
        pod.k8s_deployments[
            0
        ]._read_namespaced_deployment = lambda *args, **kwargs: client.V1Deployment(
            status=client.V1DeploymentStatus(replicas=3, ready_replicas=3)
        )
        pod.k8s_head_deployment._read_namespaced_deployment = (
            lambda *args, **kwargs: client.V1Deployment(
                status=client.V1DeploymentStatus(replicas=1, ready_replicas=1)
            )
        )
        with pod:
            pass
    else:
        # expect Number of ready replicas 1, waiting for 2 replicas to be available
        # keep waiting, and we set a small timeout-ready, raise the exception
        pod = K8sPod(args)
        pod.k8s_deployments[
            0
        ]._read_namespaced_deployment = lambda *args, **kwargs: client.V1Deployment(
            status=client.V1DeploymentStatus(replicas=3, ready_replicas=1)
        )
        pod.k8s_head_deployment._read_namespaced_deployment = (
            lambda *args, **kwargs: client.V1Deployment(
                status=client.V1DeploymentStatus(replicas=1, ready_replicas=1)
            )
        )
        with pytest.raises(jina.excepts.RuntimeFailToStart):
            with pod:
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
