from typing import Union, Dict, Tuple
import json
import pytest

from jina import __version__
from jina.helper import Namespace
from jina.hubble import HubExecutor
from jina.hubble.hubio import HubIO
from jina.parsers import set_pod_parser, set_gateway_parser
from jina.peapods.pods.config.docker_compose import DockerComposeConfig


@pytest.fixture(autouse=True)
def set_test_pip_version():
    import os

    os.environ['JINA_K8S_USE_TEST_PIP'] = 'True'
    yield
    del os.environ['JINA_K8S_USE_TEST_PIP']


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
            print(f' differ in {attr}')
            return False
    return True


@pytest.mark.parametrize('shards', [1, 5])
@pytest.mark.parametrize('replicas', [1, 5])
@pytest.mark.parametrize('uses_before', [None, 'jinahub+docker://HubBeforeExecutor'])
@pytest.mark.parametrize('uses_after', [None, 'docker://docker_after_image:latest'])
@pytest.mark.parametrize('uses_with', ['{"paramkey": "paramvalue"}', None])
@pytest.mark.parametrize('uses_metas', ['{"workspace": "workspacevalue"}', None])
def test_parse_args(
    shards: int,
    replicas: int,
    uses_with,
    uses_metas,
    uses_before,
    uses_after,
):
    args_list = [
        '--shards',
        str(shards),
        '--replicas',
        str(replicas),
        '--name',
        'executor',
    ]
    if uses_before is not None:
        args_list.extend(['--uses-before', uses_before])

    if uses_after is not None:
        args_list.extend(['--uses-after', uses_after])

    if uses_with is not None:
        args_list.extend(['--uses-with', uses_with])

    if uses_metas is not None:
        args_list.extend(['--uses-metas', uses_metas])
    args = set_pod_parser().parse_args(args_list)
    pod_config = DockerComposeConfig(args)

    assert namespace_equal(
        pod_config.services_args['head_service'],
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
            'uses_before',
            'uses_after',
            'uses_before_address',
            'uses_after_address',
            'replicas',
        ),
    )
    assert pod_config.services_args['head_service'].name == 'executor/head-0'
    assert pod_config.services_args['head_service'].runtime_cls == 'HeadRuntime'
    assert pod_config.services_args['head_service'].uses is None
    assert pod_config.services_args['head_service'].uses_before is None
    assert pod_config.services_args['head_service'].uses_after is None
    assert pod_config.services_args['head_service'].uses_metas is None
    assert pod_config.services_args['head_service'].uses_with is None
    if uses_before is None:
        assert pod_config.services_args['head_service'].uses_before_address is None
    else:
        assert (
            pod_config.services_args['head_service'].uses_before_address
            == 'executor-uses-before:8081'
        )
    if uses_after is None:
        assert pod_config.services_args['head_service'].uses_after_address is None
    else:
        assert (
            pod_config.services_args['head_service'].uses_after_address
            == 'executor-uses-after:8081'
        )
    if shards > 1:
        if replicas == 1:
            candidate_connection_list = {
                str(i): [f'executor-{i}:8081'] for i in range(shards)
            }
        else:
            candidate_connection_list = {}
            for shard_id in range(shards):
                candidate_connection_list[str(shard_id)] = []
                for replica_id in range(replicas):
                    candidate_connection_list[str(shard_id)].append(
                        f'executor-{shard_id}-rep-{replica_id}:8081'
                    )

    else:
        if replicas == 1:
            candidate_connection_list = {'0': [f'executor:8081']}
        else:
            candidate_connection_list = {'0': []}
            for replica_id in range(replicas):
                candidate_connection_list['0'].append(f'executor-rep-{replica_id}:8081')

    assert pod_config.services_args['head_service'].connection_list == json.dumps(
        candidate_connection_list
    )

    if uses_before is not None:
        assert (
            pod_config.services_args['uses_before_service'].name
            == 'executor/uses-before'
        )
        assert (
            pod_config.services_args['uses_before_service'].runtime_cls
            == 'WorkerRuntime'
        )
        assert pod_config.services_args['uses_before_service'].uses == uses_before
        assert pod_config.services_args['uses_before_service'].uses_before is None
        assert pod_config.services_args['uses_before_service'].uses_after is None
        assert pod_config.services_args['uses_before_service'].uses_metas is None
        assert pod_config.services_args['uses_before_service'].uses_with is None
        assert pod_config.services_args['uses_before_service'].shard_id == 0
        assert pod_config.services_args['uses_before_service'].replicas == 1
        assert pod_config.services_args['uses_before_service'].replica_id == -1

    if uses_after is not None:
        assert (
            pod_config.services_args['uses_after_service'].name == 'executor/uses-after'
        )
        assert (
            pod_config.services_args['uses_after_service'].runtime_cls
            == 'WorkerRuntime'
        )
        assert pod_config.services_args['uses_after_service'].uses == uses_after
        assert pod_config.services_args['uses_after_service'].uses_before is None
        assert pod_config.services_args['uses_after_service'].uses_after is None
        assert pod_config.services_args['uses_after_service'].uses_metas is None
        assert pod_config.services_args['uses_after_service'].uses_with is None
        assert pod_config.services_args['uses_after_service'].shard_id == 0
        assert pod_config.services_args['uses_after_service'].replicas == 1
        assert pod_config.services_args['uses_after_service'].replica_id == -1

    for i, depl_arg in enumerate(pod_config.services_args['services']):
        import copy

        assert (
            depl_arg.name == f'executor-{i}'
            if len(pod_config.services_args['services']) > 1
            else 'executor'
        )
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
                'name',
            ),
        )


@pytest.mark.parametrize('shards', [1, 5])
@pytest.mark.parametrize('replicas', [1, 5])
def test_parse_args_custom_executor(shards: int, replicas: int):
    uses_before = 'custom-executor-before'
    uses_after = 'custom-executor-after'
    args = set_pod_parser().parse_args(
        [
            '--shards',
            str(shards),
            '--replicas',
            str(replicas),
            '--uses-before',
            uses_before,
            '--uses-after',
            uses_after,
            '--name',
            'executor',
        ]
    )
    pod_config = DockerComposeConfig(args)

    assert pod_config.services_args['head_service'].runtime_cls == 'HeadRuntime'
    assert pod_config.services_args['head_service'].uses_before is None
    assert (
        pod_config.services_args['head_service'].uses_before_address
        == 'executor-uses-before:8081'
    )
    assert pod_config.services_args['head_service'].uses is None
    assert pod_config.services_args['head_service'].uses_after is None
    assert (
        pod_config.services_args['head_service'].uses_after_address
        == f'executor-uses-after:8081'
    )

    assert pod_config.services_args['head_service'].uses_before is None

    assert pod_config.services_args['head_service'].uses_after is None

    assert (
        pod_config.services_args['uses_before_service'].name == 'executor/uses-before'
    )
    assert (
        pod_config.services_args['uses_before_service'].runtime_cls == 'WorkerRuntime'
    )
    assert pod_config.services_args['uses_before_service'].uses == uses_before
    assert pod_config.services_args['uses_before_service'].uses_before is None
    assert pod_config.services_args['uses_before_service'].uses_after is None
    assert pod_config.services_args['uses_before_service'].uses_metas is None
    assert pod_config.services_args['uses_before_service'].uses_with is None
    assert pod_config.services_args['uses_before_service'].shard_id == 0
    assert pod_config.services_args['uses_before_service'].replicas == 1
    assert pod_config.services_args['uses_before_service'].replica_id == -1

    assert pod_config.services_args['uses_after_service'].name == 'executor/uses-after'
    assert pod_config.services_args['uses_after_service'].runtime_cls == 'WorkerRuntime'
    assert pod_config.services_args['uses_after_service'].uses == uses_after
    assert pod_config.services_args['uses_after_service'].uses_before is None
    assert pod_config.services_args['uses_after_service'].uses_after is None
    assert pod_config.services_args['uses_after_service'].uses_metas is None
    assert pod_config.services_args['uses_after_service'].uses_with is None
    assert pod_config.services_args['uses_after_service'].shard_id == 0
    assert pod_config.services_args['uses_after_service'].replicas == 1
    assert pod_config.services_args['uses_after_service'].replica_id == -1

    for i, depl_arg in enumerate(pod_config.services_args['services']):
        import copy

        assert (
            depl_arg.name == f'executor-{i}'
            if len(pod_config.services_args['services']) > 1
            else 'executor'
        )
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
                'name',
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
def test_worker_services(name: str, shards: str):
    args = set_pod_parser().parse_args(['--name', name, '--shards', shards])
    pod_config = DockerComposeConfig(args)

    actual_services = pod_config.worker_services

    assert len(actual_services) == int(shards)
    for i, deploy in enumerate(actual_services):
        if int(shards) > 1:
            assert deploy.name == f'{name}-{i}'
        else:
            assert deploy.name == name
        assert deploy.jina_pod_name == name
        assert deploy.shard_id == i


@pytest.mark.parametrize('pod_addresses', [None, {'1': 'executor-head:8081'}])
def test_docker_compose_gateway(pod_addresses):
    args = set_gateway_parser().parse_args(
        ['--env', 'ENV_VAR:ENV_VALUE', '--port-expose', '32465', '--port-in', '33455']
    )  # envs are
    # ignored for gateway
    pod_config = DockerComposeConfig(args, pod_addresses=pod_addresses)
    name, gateway_config = pod_config.to_docker_compose_config()[0]
    assert name == 'gateway'
    assert gateway_config['image'] == 'jinaai/jina:test-pip'
    assert gateway_config['entrypoint'] == ['jina']
    assert gateway_config['ports'] == [
        f'{args.port_expose}:{args.port_expose}',
        f'{args.port_in}:{args.port_in}',
    ]
    assert gateway_config['expose'] == [f'{args.port_expose}', f'{args.port_in}']
    args = gateway_config['command']
    assert args[0] == 'gateway'
    assert '--port-in' in args
    assert args[args.index('--port-in') + 1] == '33455'
    assert '--port-expose' in args
    assert args[args.index('--port-expose') + 1] == '32465'
    assert '--env' not in args
    assert '--pea-role' in args
    assert args[args.index('--pea-role') + 1] == 'GATEWAY'
    if pod_addresses is not None:
        assert '--pods-addresses' in args
        assert args[args.index('--pods-addresses') + 1] == json.dumps(pod_addresses)


@pytest.mark.parametrize('shards', [3, 1])
@pytest.mark.parametrize('replicas', [3, 1])
@pytest.mark.parametrize(
    'uses', ['jinahub+docker://HubExecutor', 'docker://docker_image:latest']
)
@pytest.mark.parametrize('uses_before', [None, 'jinahub+docker://HubBeforeExecutor'])
@pytest.mark.parametrize('uses_after', [None, 'jinahub+docker://HubAfterExecutor'])
@pytest.mark.parametrize('uses_with', ['{"paramkey": "paramvalue"}', None])
@pytest.mark.parametrize('uses_metas', ['{"workspace": "workspacevalue"}', None])
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
def test_docker_compose_yaml_regular_pod(
    uses_before,
    uses_after,
    uses,
    shards,
    replicas,
    uses_with,
    uses_metas,
    polling,
    monkeypatch,
):
    def _mock_fetch(name, tag=None, secret=None, force=False):
        return (
            HubExecutor(
                uuid='hello',
                name='alias_dummy',
                tag='v0',
                image_name=f'jinahub/{name}',
                md5sum=None,
                visibility=True,
                archive_url=None,
            ),
            False,
        )

    monkeypatch.setattr(HubIO, 'fetch_meta', _mock_fetch)
    args_list = [
        '--name',
        'executor',
        '--uses',
        uses,
        '--env',
        'ENV_VAR:ENV_VALUE',
        '--replicas',
        str(replicas),
        '--shards',
        str(shards),
        '--polling',
        str(polling),
    ]
    if uses_before is not None:
        args_list.extend(['--uses-before', uses_before])

    if uses_after is not None:
        args_list.extend(['--uses-after', uses_after])

    if uses_with is not None:
        args_list.extend(['--uses-with', uses_with])

    if uses_metas is not None:
        args_list.extend(['--uses-metas', uses_metas])

    args = set_pod_parser().parse_args(args_list)
    # ignored for gateway
    pod_config = DockerComposeConfig(args)
    yaml_configs = pod_config.to_docker_compose_config()
    assert len(yaml_configs) == 1 + shards * replicas + (1 if uses_before else 0) + (
        1 if uses_after else 0
    )
    head_name, head_config = yaml_configs[0]
    assert head_name == 'executor-head-0'
    assert head_config['image'] == 'jinaai/jina:test-pip'
    assert head_config['entrypoint'] == ['jina']
    head_args = head_config['command']
    assert head_args[0] == 'executor'
    assert '--native' in head_args
    assert '--runtime-cls' in head_args
    assert head_args[head_args.index('--runtime-cls') + 1] == 'HeadRuntime'
    assert '--name' in head_args
    assert head_args[head_args.index('--name') + 1] == 'executor/head-0'
    assert '--port-in' in head_args
    assert head_args[head_args.index('--port-in') + 1] == '8081'
    assert '--env' not in head_args
    assert '--pea-role' in head_args
    assert head_args[head_args.index('--pea-role') + 1] == 'HEAD'
    assert '--connection-list' in head_args
    connection_list_string = head_args[head_args.index('--connection-list') + 1]
    candidate_connection_list = {}
    if shards > 1:
        if replicas == 1:
            candidate_connection_list = {
                str(shard_id): [f'executor-{shard_id}:8081']
                for shard_id in range(shards)
            }
        else:
            candidate_connection_list = {}
            for shard_id in range(shards):
                candidate_connection_list[str(shard_id)] = []
                for replica_id in range(replicas):
                    candidate_connection_list[str(shard_id)].append(
                        f'executor-{shard_id}-rep-{replica_id}:8081'
                    )
    else:
        if shards == 1:
            if replicas == 1:
                candidate_connection_list = {'0': [f'executor:8081']}
            else:
                candidate_connection_list = {'0': []}
                for replica_id in range(replicas):
                    candidate_connection_list['0'].append(
                        f'executor-rep-{replica_id}:8081'
                    )

    assert connection_list_string == json.dumps(candidate_connection_list)

    if polling == 'ANY':
        assert '--polling' not in head_args
    else:
        assert '--polling' in head_args
        assert head_args[head_args.index('--polling') + 1] == 'ALL'

    if uses_before is not None:
        uses_before_name, uses_before_config = yaml_configs[1]
        assert uses_before_name == 'executor-uses-before'
        assert uses_before_config['image'] == 'jinahub/HubBeforeExecutor'
        assert uses_before_config['entrypoint'] == ['jina']
        uses_before_args = uses_before_config['command']
        assert uses_before_args[0] == 'executor'
        assert '--native' in uses_before_args
        assert '--name' in uses_before_args
        assert '--env' not in uses_before_args
        assert (
            uses_before_args[uses_before_args.index('--name') + 1]
            == 'executor/uses-before'
        )
        assert '--port-in' in uses_before_args
        assert uses_before_args[uses_before_args.index('--port-in') + 1] == '8081'
        assert '--connection-list' not in uses_before_args
        assert '--polling' not in uses_before_args

    if uses_after is not None:
        uses_after_name, uses_after_config = (
            yaml_configs[1] if uses_before is None else yaml_configs[2]
        )
        assert uses_after_name == 'executor-uses-after'
        assert uses_after_config['image'] == 'jinahub/HubAfterExecutor'
        assert uses_after_config['entrypoint'] == ['jina']
        uses_after_args = uses_after_config['command']
        assert uses_after_args[0] == 'executor'
        assert '--native' in uses_after_args
        assert '--name' in uses_after_args
        assert '--env' not in uses_after_args
        assert (
            uses_after_args[uses_after_args.index('--name') + 1]
            == 'executor/uses-after'
        )
        assert '--port-in' in uses_after_args
        assert uses_after_args[uses_after_args.index('--port-in') + 1] == '8081'
        assert '--connection-list' not in uses_after_args
        assert '--polling' not in uses_after_args

    num_shards_replicas_configs = shards * replicas
    shards_replicas_configs = yaml_configs[-num_shards_replicas_configs:]
    for shard_id in range(shards):
        replicas_configs = shards_replicas_configs[
            shard_id * replicas : shard_id * replicas + replicas
        ]
        for replica_id, (replica_name, replica_config) in enumerate(replicas_configs):
            expected_name = 'executor'
            expected_arg_name = 'executor'
            if shards > 1:
                expected_name += f'-{shard_id}'
                expected_arg_name += f'-{shard_id}'
            if replicas > 1:
                expected_name += f'-rep-{replica_id}'
                expected_arg_name += f'/rep-{replica_id}'
            assert replica_name == expected_name
            assert (
                replica_config['image'] == 'docker_image:latest'
                if uses == 'docker_image:latest'
                else 'jinahub/HubExecutor'
            )
            assert replica_config['entrypoint'] == ['jina']
            replica_args = replica_config['command']
            assert replica_args[0] == 'executor'
            assert '--native' in replica_args
            assert '--name' in replica_args
            assert replica_args[replica_args.index('--name') + 1] == expected_arg_name
            assert '--port-in' in replica_args
            assert replica_args[replica_args.index('--port-in') + 1] == '8081'
            assert '--env' in replica_args
            assert (
                replica_args[replica_args.index('--env') + 1]
                == '{"ENV_VAR": "ENV_VALUE"}'
            )
            assert '--connection-list' not in replica_args
            if uses_with is not None:
                assert '--uses-with' in replica_args
                assert replica_args[replica_args.index('--uses-with') + 1] == uses_with
            else:
                assert '--uses-with' not in replica_args

            expected_uses_metas = {}
            if uses_metas is not None:
                expected_uses_metas = json.loads(uses_metas)
            expected_uses_metas['pea_id'] = shard_id
            assert '--uses-metas' in replica_args
            assert replica_args[replica_args.index('--uses-metas') + 1] == json.dumps(
                expected_uses_metas
            )
