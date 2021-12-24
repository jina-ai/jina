from typing import Union, Dict, Tuple
import json
import pytest

from jina import __version__
from jina.helper import Namespace
from jina.parsers import set_pod_parser, set_gateway_parser
from jina.peapods.networking import K8sGrpcConnectionPool
from jina.peapods.pods.config.k8s import _get_base_executor_version, K8sPodConfig


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


@pytest.mark.parametrize('shards', [1, 5])
@pytest.mark.parametrize('uses_before', [None, 'jinahub+docker://HubBeforeExecutor'])
@pytest.mark.parametrize('uses_after', [None, 'docker://docker_after_image:latest'])
@pytest.mark.parametrize('k8s_connection_pool_call', [False, True])
@pytest.mark.parametrize('uses_with', ['{"paramkey": "paramvalue"}', None])
@pytest.mark.parametrize('uses_metas', ['{"workspace": "workspacevalue"}', None])
def test_parse_args(
    shards: int,
    k8s_connection_pool_call: bool,
    uses_with,
    uses_metas,
    uses_before,
    uses_after,
):
    args_list = ['--shards', str(shards), '--name', 'executor']
    if uses_before is not None:
        args_list.extend(['--uses-before', uses_before])

    if uses_after is not None:
        args_list.extend(['--uses-after', uses_after])

    if uses_with is not None:
        args_list.extend(['--uses-with', uses_with])

    if uses_metas is not None:
        args_list.extend(['--uses-metas', uses_metas])
    args = set_pod_parser().parse_args(args_list)
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
            'uses_with',
            'uses_metas',
            'uses_before_address',
            'uses_after_address',
        ),
    )
    assert (
        pod_config.deployment_args['head_deployment'].k8s_namespace
        == 'default-namespace'
    )
    assert pod_config.deployment_args['head_deployment'].name == 'executor/head-0'
    assert pod_config.deployment_args['head_deployment'].runtime_cls == 'HeadRuntime'
    assert pod_config.deployment_args['head_deployment'].uses is None
    assert pod_config.deployment_args['head_deployment'].uses_before == uses_before
    assert pod_config.deployment_args['head_deployment'].uses_after == uses_after
    assert pod_config.deployment_args['head_deployment'].uses_metas is None
    assert pod_config.deployment_args['head_deployment'].uses_with is None
    assert (
        pod_config.deployment_args['head_deployment'].k8s_connection_pool
        is k8s_connection_pool_call
    )
    if uses_before is None:
        assert pod_config.deployment_args['head_deployment'].uses_before_address is None
    else:
        assert (
            pod_config.deployment_args['head_deployment'].uses_before_address
            == '127.0.0.1:8082'
        )
    if uses_after is None:
        assert pod_config.deployment_args['head_deployment'].uses_after_address is None
    else:
        assert (
            pod_config.deployment_args['head_deployment'].uses_after_address
            == '127.0.0.1:8083'
        )
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
                'uses_before',  # the uses_before and after is head business
                'uses_after',
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
        assert deploy.jina_pod_name == name
        assert deploy.shard_id == i
        assert deploy.k8s_connection_pool is k8s_connection_pool_call


def assert_role_config(role: Dict):
    assert role['kind'] == 'Role'
    assert role['metadata'] == {
        'namespace': 'default-namespace',
        'name': 'connection-pool',
    }
    assert role['rules'] == [
        {
            'apiGroups': [''],
            'resources': ['pods', 'services'],
            'verbs': ['list', 'watch'],
        }
    ]


def assert_role_binding_config(role_binding: Dict):
    assert role_binding['kind'] == 'RoleBinding'
    assert role_binding['metadata'] == {
        'name': 'connection-pool-binding',
        'namespace': 'default-namespace',
    }
    assert role_binding['subjects'] == [
        {'kind': 'ServiceAccount', 'name': 'default', 'apiGroup': ''}
    ]
    assert role_binding['roleRef'] == {
        'kind': 'Role',
        'name': 'connection-pool',
        'apiGroup': '',
    }


def assert_config_map_config(config_map: Dict, base_name: str):
    assert config_map['kind'] == 'ConfigMap'
    assert config_map['metadata'] == {
        'name': f'{base_name}-configmap',
        'namespace': 'default-namespace',
    }
    assert config_map['data'] == {
        'ENV_VAR': 'ENV_VALUE',
        'JINA_LOG_LEVEL': 'DEBUG',
        'pythonunbuffered': '1',
        'worker_class': 'uvicorn.workers.UvicornH11Worker',
    }


@pytest.mark.parametrize('pod_addresses', [None, {'1': 'address.svc'}])
@pytest.mark.parametrize('k8s_connection_pool_call', [False, True])
def test_k8s_yaml_gateway(k8s_connection_pool_call, pod_addresses):
    args = set_gateway_parser().parse_args(
        ['--env', 'ENV_VAR:ENV_VALUE', '--port-expose', '32465']
    )  # envs are
    # ignored for gateway
    pod_config = K8sPodConfig(
        args, 'default-namespace', k8s_connection_pool_call, pod_addresses
    )
    yaml_configs = pod_config.to_k8s_yaml()
    assert len(yaml_configs) == 1
    name, configs = yaml_configs[0]
    assert name == 'gateway'
    assert (
        len(configs) == 5
    )  # 5 configs per yaml (connection-pool, conneciton-pool-role, configmap, service and
    # deployment)
    role = configs[0]
    assert_role_config(role)

    role_binding = configs[1]
    assert_role_binding_config(role_binding)
    config_map = configs[2]
    assert_config_map_config(config_map, 'gateway')
    service = configs[3]
    assert service['kind'] == 'Service'
    assert service['metadata'] == {
        'name': 'gateway',
        'namespace': 'default-namespace',
        'labels': {'app': 'gateway'},
    }
    spec_service = service['spec']
    assert spec_service['type'] == 'ClusterIP'
    assert len(spec_service['ports']) == 2
    port_expose = spec_service['ports'][0]
    assert port_expose['name'] == 'port-expose'
    assert port_expose['protocol'] == 'TCP'
    assert port_expose['port'] == 32465
    assert port_expose['targetPort'] == 32465
    port_in = spec_service['ports'][1]
    assert port_in['name'] == 'port-in'
    assert port_in['protocol'] == 'TCP'
    assert port_in['port'] == 8081
    assert port_in['targetPort'] == 8081
    assert spec_service['selector'] == {'app': 'gateway'}

    deployment = configs[4]
    assert deployment['kind'] == 'Deployment'
    assert deployment['metadata'] == {
        'name': 'gateway',
        'namespace': 'default-namespace',
    }
    spec_deployment = deployment['spec']
    assert spec_deployment['replicas'] == 1  # no gateway replication for now
    assert spec_deployment['strategy'] == {
        'type': 'RollingUpdate',
        'rollingUpdate': {'maxSurge': 1, 'maxUnavailable': 0},
    }
    assert spec_deployment['selector'] == {'matchLabels': {'app': 'gateway'}}
    template = spec_deployment['template']
    assert template['metadata'] == {
        'labels': {
            'app': 'gateway',
            'jina_pod_name': 'gateway',
            'shard_id': '',
            'pea_type': 'gateway',
            'ns': 'default-namespace',
        }
    }
    spec = template['spec']
    containers = spec['containers']
    assert len(containers) == 1
    container = containers[0]
    assert container['name'] == 'executor'
    assert container['image'] == 'jinaai/jina:test-pip'
    assert container['imagePullPolicy'] == 'IfNotPresent'
    assert container['command'] == ['jina']
    args = container['args']
    assert args[0] == 'gateway'
    assert '--k8s-namespace' in args
    assert args[args.index('--k8s-namespace') + 1] == 'default-namespace'
    assert '--port-in' in args
    assert args[args.index('--port-in') + 1] == '8081'
    assert '--port-expose' in args
    assert args[args.index('--port-expose') + 1] == '32465'
    assert '--env' in args
    assert args[args.index('--env') + 1] == '{"ENV_VAR": "ENV_VALUE"}'
    assert '--pea-role' in args
    assert args[args.index('--pea-role') + 1] == 'GATEWAY'
    if not k8s_connection_pool_call:
        assert args[-1] == '--k8s-disable-connection-pool'
    if pod_addresses is not None:
        assert '--pods-addresses' in args
        assert args[args.index('--pods-addresses') + 1] == json.dumps(pod_addresses)
    else:
        assert '--pods-addresses' not in args


def assert_port_config(port_dict: Dict, name: str, port: int):
    assert port_dict['name'] == name
    assert port_dict['protocol'] == 'TCP'
    assert port_dict['port'] == port
    assert port_dict['targetPort'] == port


@pytest.mark.parametrize('uses_before', [None, 'jinahub+docker://HubBeforeExecutor'])
@pytest.mark.parametrize('uses_after', [None, 'jinahub+docker://HubAfterExecutor'])
@pytest.mark.parametrize(
    'uses', ['jinahub+docker://HubExecutor', 'docker://docker_image:latest']
)
@pytest.mark.parametrize('shards', [1, 3])
@pytest.mark.parametrize('k8s_connection_pool_call', [False, True])
@pytest.mark.parametrize('uses_with', ['{"paramkey": "paramvalue"}', None])
@pytest.mark.parametrize('uses_metas', ['{"workspace": "workspacevalue"}', None])
def test_k8s_yaml_regular_pod(
    uses_before,
    uses_after,
    uses,
    shards,
    k8s_connection_pool_call,
    uses_with,
    uses_metas,
):
    args_list = [
        '--name',
        'executor',
        '--uses',
        uses,
        '--env',
        'ENV_VAR:ENV_VALUE',
        '--replicas',
        '3',
        '--shards',
        str(shards),
    ]
    if uses_before is not None:
        args_list.extend(['--uses-before', uses_before])

    if uses_after is not None:
        args_list.extend(['--uses-after', uses_after])

    if uses_with is not None:
        args_list.extend(['--uses-with', uses_with])

    if uses_metas is not None:
        args_list.extend(['--uses-metas', uses_metas])

    print(f' args_list {args_list}')

    args = set_pod_parser().parse_args(args_list)
    # ignored for gateway
    pod_config = K8sPodConfig(args, 'default-namespace', k8s_connection_pool_call)
    yaml_configs = pod_config.to_k8s_yaml()
    assert len(yaml_configs) == 1 + shards
    head_name, head_configs = yaml_configs[0]
    assert head_name == 'executor/head-0'
    assert (
        len(head_configs) == 5
    )  # 5 configs per yaml (connection-pool, conneciton-pool-role, configmap, service and
    role = head_configs[0]
    assert_role_config(role)
    role_binding = head_configs[1]
    assert_role_binding_config(role_binding)
    config_map = head_configs[2]
    assert_config_map_config(config_map, 'executor-head-0')
    head_service = head_configs[3]
    assert head_service['kind'] == 'Service'
    assert head_service['metadata'] == {
        'name': 'executor-head-0',
        'namespace': 'default-namespace',
        'labels': {'app': 'executor-head-0'},
    }
    head_spec_service = head_service['spec']
    assert head_spec_service['type'] == 'ClusterIP'
    assert len(head_spec_service['ports']) == 2
    head_port_expose = head_spec_service['ports'][0]
    assert_port_config(head_port_expose, 'port-expose', 8080)
    head_port_in = head_spec_service['ports'][1]
    assert_port_config(head_port_in, 'port-in', 8081)
    assert head_spec_service['selector'] == {'app': 'executor-head-0'}

    head_deployment = head_configs[4]
    assert head_deployment['kind'] == 'Deployment'
    assert head_deployment['metadata'] == {
        'name': 'executor-head-0',
        'namespace': 'default-namespace',
    }
    head_spec_deployment = head_deployment['spec']
    assert head_spec_deployment['replicas'] == 1  # no head replication for now
    assert head_spec_deployment['strategy'] == {
        'type': 'RollingUpdate',
        'rollingUpdate': {'maxSurge': 1, 'maxUnavailable': 0},
    }
    assert head_spec_deployment['selector'] == {
        'matchLabels': {'app': 'executor-head-0'}
    }
    head_template = head_spec_deployment['template']
    assert head_template['metadata'] == {
        'labels': {
            'app': 'executor-head-0',
            'jina_pod_name': 'executor',
            'shard_id': '',
            'pea_type': 'head',
            'ns': 'default-namespace',
        }
    }

    head_spec = head_template['spec']
    head_containers = head_spec['containers']
    assert len(head_containers) == 1 + (1 if uses_before is not None else 0) + (
        1 if uses_after is not None else 0
    )
    head_runtime_container = head_containers[0]
    assert head_runtime_container['name'] == 'executor'
    assert head_runtime_container['image'] == 'jinaai/jina:test-pip'
    assert head_runtime_container['imagePullPolicy'] == 'IfNotPresent'
    assert head_runtime_container['command'] == ['jina']
    head_runtime_container_args = head_runtime_container['args']
    print(f' head_runtime_container_args {head_runtime_container_args}')

    assert head_runtime_container_args[0] == 'executor'
    assert '--native' in head_runtime_container_args
    assert '--runtime-cls' in head_runtime_container_args
    assert (
        head_runtime_container_args[
            head_runtime_container_args.index('--runtime-cls') + 1
        ]
        == 'HeadRuntime'
    )
    assert '--name' in head_runtime_container_args
    assert (
        head_runtime_container_args[head_runtime_container_args.index('--name') + 1]
        == 'executor/head-0'
    )
    assert '--k8s-namespace' in head_runtime_container_args
    assert (
        head_runtime_container_args[
            head_runtime_container_args.index('--k8s-namespace') + 1
        ]
        == 'default-namespace'
    )
    assert '--port-in' in head_runtime_container_args
    assert (
        head_runtime_container_args[head_runtime_container_args.index('--port-in') + 1]
        == '8081'
    )
    assert '--env' in head_runtime_container_args
    assert (
        head_runtime_container_args[head_runtime_container_args.index('--env') + 1]
        == '{"ENV_VAR": "ENV_VALUE"}'
    )
    assert '--pea-role' in head_runtime_container_args
    assert (
        head_runtime_container_args[head_runtime_container_args.index('--pea-role') + 1]
        == 'HEAD'
    )
    if not k8s_connection_pool_call:
        assert '--k8s-disable-connection-pool' in head_runtime_container_args
        assert '--connection-list' in head_runtime_container_args
        connection_list_string = head_runtime_container_args[
            head_runtime_container_args.index('--connection-list') + 1
        ]
        if shards > 1:
            assert connection_list_string == json.dumps(
                {
                    str(shard_id): f'executor-{shard_id}.default-namespace.svc:8081'
                    for shard_id in range(shards)
                }
            )
        else:
            assert connection_list_string == json.dumps(
                {'0': 'executor.default-namespace.svc:8081'}
            )

    if uses_before is not None:
        uses_before_container = head_containers[1]
        assert uses_before_container['name'] == 'uses-before'
        assert uses_before_container['image'] == 'jinahub+HubBeforeExecutor'
        assert uses_before_container['imagePullPolicy'] == 'IfNotPresent'
        assert uses_before_container['command'] == ['jina']
        uses_before_runtime_container_args = uses_before_container['args']
        print(
            f' uses_before_runtime_container_args {uses_before_runtime_container_args}'
        )

        assert uses_before_runtime_container_args[0] == 'executor'
        assert '--native' in uses_before_runtime_container_args
        assert '--runtime-cls' in uses_before_runtime_container_args
        assert '--uses' in uses_before_runtime_container_args
        assert (
            uses_before_runtime_container_args[
                uses_before_runtime_container_args.index('--uses') + 1
            ]
            == 'config.yml'
        )
        assert (
            uses_before_runtime_container_args[
                uses_before_runtime_container_args.index('--runtime-cls') + 1
            ]
            == 'WorkerRuntime'
        )
        assert '--name' in uses_before_runtime_container_args
        assert (
            uses_before_runtime_container_args[
                uses_before_runtime_container_args.index('--name') + 1
            ]
            == 'executor/head-0'
        )
        assert '--k8s-namespace' in uses_before_runtime_container_args
        assert (
            uses_before_runtime_container_args[
                uses_before_runtime_container_args.index('--k8s-namespace') + 1
            ]
            == 'default-namespace'
        )
        assert '--port-in' in uses_before_runtime_container_args
        assert (
            uses_before_runtime_container_args[
                uses_before_runtime_container_args.index('--port-in') + 1
            ]
            == '8081'
        )
        assert '--env' in uses_before_runtime_container_args
        assert (
            uses_before_runtime_container_args[
                uses_before_runtime_container_args.index('--env') + 1
            ]
            == '{"ENV_VAR": "ENV_VALUE"}'
        )
        assert '--pea-role' in uses_before_runtime_container_args
        assert (
            uses_before_runtime_container_args[
                uses_before_runtime_container_args.index('--pea-role') + 1
            ]
            == 'HEAD'
        )
        assert '--connection-list' not in uses_before_runtime_container_args
        if not k8s_connection_pool_call:
            assert '--k8s-disable-connection-pool' in uses_before_runtime_container_args

    # if uses_metas is not None:
    #     assert '--uses-metas' in head_runtime_container_args
    #     assert head_runtime_container_args[head_runtime_container_args.index('--uses-metas') + 1] == '{"workspace": ' \
    #                                                                                                  '"workspacevalue"} '
    # head_runtime_container = containers[0]
    # assert container['name'] == 'executor'
    # assert container['image'] == 'jinaai/jina:master-py38-standard'
    # assert container['imagePullPolicy'] == 'IfNotPresent'
    # assert container['command'] == ['jina']
    # args = container['args']
    # assert len(configs) == 5  # 5 configs per yaml (connection-pool, conneciton-pool-role, configmap, service and
    # # deployment)
    # role = configs[0]
    # assert role['kind'] == 'Role'
    # assert role['metadata'] == {'namespace': 'default-namespace', 'name': 'connection-pool'}
    # assert role['rules'] == [{'apiGroups': [''], 'resources': ['pods', 'services'], 'verbs': ['list', 'watch']}]
    #
    # role_binding = configs[1]
    # assert role_binding['kind'] == 'RoleBinding'
    # assert role_binding['metadata'] == {'name': 'connection-pool-binding', 'namespace': 'default-namespace'}
    # assert role_binding['subjects'] == [{'kind': 'ServiceAccount', 'name': 'default', 'apiGroup': ''}]
    # assert role_binding['roleRef'] == {'kind': 'Role', 'name': 'connection-pool', 'apiGroup': ''}
    #
    # config_map = configs[2]
    # assert config_map['kind'] == 'ConfigMap'
    # assert config_map['metadata'] == {'name': 'gateway-configmap', 'namespace': 'default-namespace'}
    # assert config_map['data'] == {'JINA_LOG_LEVEL': 'DEBUG', 'pythonunbuffered': '1',
    #                               'worker_class': 'uvicorn.workers.UvicornH11Worker'}
    #
    # service = configs[3]
    # assert service['kind'] == 'Service'
    # assert service['metadata'] == {'name': 'gateway', 'namespace': 'default-namespace', 'labels': {'app': 'gateway'}}
    # spec_service = service['spec']
    # assert spec_service['type'] == 'ClusterIP'
    # assert len(spec_service['ports']) == 2
    # port_expose = spec_service['ports'][0]
    # assert port_expose['name'] == 'port-expose'
    # assert port_expose['protocol'] == 'TCP'
    # assert port_expose['port'] == 32465
    # assert port_expose['targetPort'] == 32465
    # port_in = spec_service['ports'][1]
    # assert port_in['name'] == 'port-in'
    # assert port_in['protocol'] == 'TCP'
    # assert port_in['port'] == 8081
    # assert port_in['targetPort'] == 8081
    # assert spec_service['ports'][1]['name'] == 'port-in'
    # assert spec_service['ports'][1]['protocol'] == 'TCP'
    # assert spec_service['selector'] == {'app': 'gateway'}
    #
    # deployment = configs[4]
    # assert deployment['kind'] == 'Deployment'
    # assert deployment['metadata'] == {'name': 'gateway', 'namespace': 'default-namespace'}
    # spec_deployment = deployment['spec']
    # assert spec_deployment['replicas'] == 1  # no gateway replication for now
    # assert spec_deployment['strategy'] == {'type': 'RollingUpdate',
    #                                        'rollingUpdate': {'maxSurge': 1, 'maxUnavailable': 0}}
    # assert spec_deployment['selector'] == {'matchLabels': {'app': 'gateway'}}
    # template = spec_deployment['template']
    # assert template['metadata'] == {
    #     'labels': {'app': 'gateway', 'jina_pod_name': 'gateway', 'shard_id': '', 'pea_type': 'gateway',
    #                'ns': 'default-namespace'}}
    # spec = template['spec']
    # containers = spec['containers']
    # assert len(containers) == 1
    # container = containers[0]
    # assert container['name'] == 'executor'
    # assert container['image'] == 'jinaai/jina:master-py38-standard'
    # assert container['imagePullPolicy'] == 'IfNotPresent'
    # assert container['command'] == ['jina']
    # args = container['args']
    #
    # assert args[0] == 'gateway'
    # assert '--k8s-namespace' in args
    # assert args[args.index('--k8s-namespace') + 1] == 'default-namespace'
    # assert '--port-in' in args
    # assert args[args.index('--port-in') + 1] == '8081'
    # assert '--port-expose' in args
    # assert args[args.index('--port-expose') + 1] == '32465'
    # assert '--env' in args
    # assert args[args.index('--env') + 1] == '{"ENV_VAR": "ENV_VALUE"}'
    # assert '--pea-role' in args
    # assert args[args.index('--pea-role') + 1] == 'GATEWAY'
    # if not k8s_connection_pool_call:
    #     assert args[-1] == '--k8s-disable-connection-pool'
