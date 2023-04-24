import json
import os
from pathlib import Path
from unittest import mock

import pytest
import yaml

from jina import Flow
from jina.constants import __cache_path__


@pytest.mark.parametrize('protocol', ['http', 'grpc'])
def test_flow_to_docker_compose_yaml(tmpdir, protocol):
    flow = (
        Flow(name='test-flow', port=9090, protocol=protocol)
        .add(name='executor0', uses_with={'param': 0})
        .add(name='executor1', shards=2, uses_with={'param': 0})
        .add(
            replicas=2,
            name='executor2',
            shards=2,
            uses_before='docker://image',
            uses_after='docker://image',
            uses_with={'param': 0},
        )
    )

    dump_path = os.path.join(str(tmpdir), 'test_flow_docker_compose.yml')

    flow.to_docker_compose_yaml(
        output_path=dump_path,
    )

    configuration = None
    with open(dump_path, encoding='utf-8') as f:
        configuration = yaml.safe_load(f)

    assert set(configuration.keys()) == {'version', 'services', 'networks'}
    assert configuration['version'] == '3.3'
    assert configuration['networks'] == {'jina-network': {'driver': 'bridge'}}
    services = configuration['services']
    assert len(services) == 12
    assert set(services.keys()) == {
        'gateway',
        'executor0',
        'executor1-head',
        'executor1-0',
        'executor1-1',
        'executor2-head',
        'executor2-0-rep-0',
        'executor2-0-rep-1',
        'executor2-1-rep-0',
        'executor2-1-rep-1',
        'executor2-uses-before',
        'executor2-uses-after',
    }

    gateway_service = services['gateway']
    assert gateway_service['entrypoint'] == ['jina']
    assert gateway_service['expose'] == [9090]
    assert gateway_service['ports'] == ['9090:9090']
    gateway_args = gateway_service['command']
    assert gateway_args[0] == 'gateway'
    assert '--port' in gateway_args
    assert gateway_args[gateway_args.index('--port') + 1] == '9090'
    assert '--graph-description' in gateway_args
    assert (
        gateway_args[gateway_args.index('--graph-description') + 1]
        == '{"executor0": ["executor1"], "start-gateway": ["executor0"], "executor1": ["executor2"], "executor2": ["end-gateway"]}'
    )
    assert '--deployments-addresses' in gateway_args
    assert (
        gateway_args[gateway_args.index('--deployments-addresses') + 1]
        == '{"executor0": ["executor0:8081"], "executor1": ["executor1-head:8081"], "executor2": ["executor2-head:8081"]}'
    )
    if protocol == 'http':
        assert '--protocol' in gateway_args
        assert gateway_args[gateway_args.index('--protocol') + 1] == 'HTTP'
    else:
        assert '--protocol' not in gateway_args
    assert '--uses-with' not in gateway_args
    assert '--env' not in gateway_args

    executor0_service = services['executor0']
    assert executor0_service['entrypoint'] == ['jina']
    assert 'expose' not in executor0_service
    executor0_args = executor0_service['command']
    assert executor0_args[0] == 'executor'
    assert '--name' in executor0_args
    assert executor0_args[executor0_args.index('--name') + 1] == 'executor0'
    assert '--uses-with' in executor0_args
    assert executor0_args[executor0_args.index('--uses-with') + 1] == '{"param": 0}'
    assert '--native' in executor0_args
    assert '--pod-role' not in executor0_args
    assert '--runtime-cls' not in executor0_args
    assert '--connection-list' not in executor0_args
    assert '--uses-before' not in executor0_args
    assert '--uses-after' not in executor0_args

    executor1_head_service = services['executor1-head']
    assert executor1_head_service['entrypoint'] == ['jina']
    assert 'expose' not in executor1_head_service
    executor1_head_args = executor1_head_service['command']
    assert executor1_head_args[0] == 'executor'
    assert '--name' in executor1_head_args
    assert (
        executor1_head_args[executor1_head_args.index('--name') + 1] == 'executor1/head'
    )
    assert '--runtime-cls' in executor1_head_args
    assert (
        executor1_head_args[executor1_head_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pod-role' in executor1_head_args
    assert executor1_head_args[executor1_head_args.index('--pod-role') + 1] == 'HEAD'
    assert '--native' in executor1_head_args
    assert '--connection-list' in executor1_head_args
    assert (
        executor1_head_args[executor1_head_args.index('--connection-list') + 1]
        == '{"0": ["executor1-0:8081"], "1": ["executor1-1:8081"]}'
    )
    assert '--uses-with' not in executor1_head_args
    assert '--uses-before' not in executor1_head_args
    assert '--uses-after' not in executor1_head_args
    assert '--envs' not in executor1_head_args
    assert '--uses-before-address' not in executor1_head_args
    assert '--uses-after-address' not in executor1_head_args

    executor1_0_service = services['executor1-0']
    assert executor1_0_service['entrypoint'] == ['jina']
    assert 'expose' not in executor1_0_service
    executor1_shard0_args = executor1_0_service['command']
    assert executor1_shard0_args[0] == 'executor'
    assert '--name' in executor1_shard0_args
    assert (
        executor1_shard0_args[executor1_shard0_args.index('--name') + 1]
        == 'executor1-0'
    )
    assert '--uses-with' in executor1_shard0_args
    assert (
        executor1_shard0_args[executor1_shard0_args.index('--uses-with') + 1]
        == '{"param": 0}'
    )
    assert '--uses-metas' in executor1_shard0_args
    assert '--native' in executor1_shard0_args
    assert '--pod-role' not in executor1_shard0_args
    assert '--runtime-cls' not in executor1_shard0_args
    assert '--connection-list' not in executor1_shard0_args
    assert '--uses-before' not in executor1_shard0_args
    assert '--uses-after' not in executor1_shard0_args

    executor1_1_service = services['executor1-1']
    assert executor1_1_service['entrypoint'] == ['jina']
    assert 'expose' not in executor1_1_service
    executor1_shard1_args = executor1_1_service['command']
    assert executor1_shard1_args[0] == 'executor'
    assert '--name' in executor1_shard1_args
    assert (
        executor1_shard1_args[executor1_shard1_args.index('--name') + 1]
        == 'executor1-1'
    )
    assert '--uses-with' in executor1_shard1_args
    assert (
        executor1_shard1_args[executor1_shard1_args.index('--uses-with') + 1]
        == '{"param": 0}'
    )
    assert '--uses-metas' in executor1_shard1_args
    assert '--native' in executor1_shard1_args
    assert '--pod-role' not in executor1_shard1_args
    assert '--runtime-cls' not in executor1_shard1_args
    assert '--connection-list' not in executor1_shard1_args
    assert '--uses-before' not in executor1_shard1_args
    assert '--uses-after' not in executor1_shard1_args

    executor2_head_service = services['executor2-head']
    assert executor2_head_service['entrypoint'] == ['jina']
    assert 'expose' not in executor2_head_service
    executor2_head_args = executor2_head_service['command']
    assert executor2_head_args[0] == 'executor'
    assert '--name' in executor2_head_args
    assert (
        executor2_head_args[executor2_head_args.index('--name') + 1] == 'executor2/head'
    )
    assert '--runtime-cls' in executor2_head_args
    assert (
        executor2_head_args[executor2_head_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pod-role' in executor2_head_args
    assert executor2_head_args[executor2_head_args.index('--pod-role') + 1] == 'HEAD'
    assert '--native' in executor2_head_args
    assert '--connection-list' in executor2_head_args
    assert executor2_head_args[executor2_head_args.index('--connection-list') + 1] == (
        '{"0": ["executor2-0-rep-0:8081", "executor2-0-rep-1:8081"],'
        ' "1": '
        '["executor2-1-rep-0:8081", "executor2-1-rep-1:8081"]}'
    )
    assert '--uses-with' not in executor2_head_args
    assert '--uses-before' not in executor2_head_args
    assert '--uses-after' not in executor2_head_args
    assert '--envs' not in executor2_head_args
    assert '--uses-before-address' in executor2_head_args
    assert (
        executor2_head_args[executor2_head_args.index('--uses-before-address') + 1]
        == 'executor2-uses-before:8081'
    )
    assert '--uses-after-address' in executor2_head_args
    assert (
        executor2_head_args[executor2_head_args.index('--uses-after-address') + 1]
        == 'executor2-uses-after:8081'
    )

    executor2_0_rep_0_service = services['executor2-0-rep-0']
    assert executor2_0_rep_0_service['entrypoint'] == ['jina']
    assert 'expose' not in executor2_0_rep_0_service
    executor2_0_rep_0_args = executor2_0_rep_0_service['command']
    assert executor2_0_rep_0_args[0] == 'executor'
    assert '--name' in executor2_0_rep_0_args
    assert (
        executor2_0_rep_0_args[executor2_0_rep_0_args.index('--name') + 1]
        == 'executor2-0/rep-0'
    )
    assert '--uses-with' in executor2_0_rep_0_args
    assert (
        executor2_0_rep_0_args[executor2_0_rep_0_args.index('--uses-with') + 1]
        == '{"param": 0}'
    )
    assert '--native' in executor2_0_rep_0_args
    assert '--pod-role' not in executor2_0_rep_0_args
    assert '--runtime-cls' not in executor2_0_rep_0_args
    assert '--connection-list' not in executor2_0_rep_0_args
    assert '--uses-before' not in executor2_0_rep_0_args
    assert '--uses-after' not in executor2_0_rep_0_args

    executor2_0_rep_1_service = services['executor2-0-rep-1']
    assert executor2_0_rep_1_service['entrypoint'] == ['jina']
    assert 'expose' not in executor2_0_rep_1_service
    executor2_0_rep_1_args = executor2_0_rep_1_service['command']
    assert executor2_0_rep_1_args[0] == 'executor'
    assert '--name' in executor2_0_rep_1_args
    assert (
        executor2_0_rep_1_args[executor2_0_rep_1_args.index('--name') + 1]
        == 'executor2-0/rep-1'
    )
    assert '--uses-with' in executor2_0_rep_1_args
    assert (
        executor2_0_rep_1_args[executor2_0_rep_1_args.index('--uses-with') + 1]
        == '{"param": 0}'
    )
    assert '--native' in executor2_0_rep_1_args
    assert '--pod-role' not in executor2_0_rep_1_args
    assert '--runtime-cls' not in executor2_0_rep_1_args
    assert '--connection-list' not in executor2_0_rep_1_args
    assert '--uses-before' not in executor2_0_rep_1_args
    assert '--uses-after' not in executor2_0_rep_1_args

    executor2_uses_before_service = services['executor2-uses-before']
    assert executor2_uses_before_service['entrypoint'] == ['jina']
    assert executor2_uses_before_service['image'] == 'image'
    assert 'expose' not in executor2_uses_before_service
    executor2_uses_before_args = executor2_uses_before_service['command']
    assert '--name' in executor2_uses_before_args
    assert (
        executor2_uses_before_args[executor2_uses_before_args.index('--name') + 1]
        == 'executor2/uses-before'
    )
    assert '--uses-with' not in executor2_uses_before_args
    assert '--uses-metas' in executor2_uses_before_args
    assert (
        executor2_uses_before_args[executor2_uses_before_args.index('--uses-metas') + 1]
        == '{}'
    )
    assert '--native' in executor2_uses_before_args
    assert '--pod-role' not in executor2_uses_before_args
    assert '--runtime-cls' not in executor2_uses_before_args
    assert '--connection-list' not in executor2_uses_before_args
    assert '--uses-before' not in executor2_uses_before_args
    assert '--uses-after' not in executor2_uses_before_args

    executor2_uses_after_service = services['executor2-uses-after']
    assert executor2_uses_after_service['entrypoint'] == ['jina']
    assert executor2_uses_after_service['image'] == 'image'
    assert 'expose' not in executor2_uses_after_service
    executor2_uses_after_args = executor2_uses_after_service['command']
    assert '--name' in executor2_uses_after_args
    assert (
        executor2_uses_after_args[executor2_uses_after_args.index('--name') + 1]
        == 'executor2/uses-after'
    )
    assert '--uses-with' not in executor2_uses_after_args
    assert '--uses-metas' in executor2_uses_after_args
    assert (
        executor2_uses_after_args[executor2_uses_after_args.index('--uses-metas') + 1]
        == '{}'
    )
    assert '--native' in executor2_uses_after_args
    assert '--pod-role' not in executor2_uses_after_args
    assert '--runtime-cls' not in executor2_uses_after_args
    assert '--connection-list' not in executor2_uses_after_args
    assert '--uses-before' not in executor2_uses_after_args
    assert '--uses-after' not in executor2_uses_after_args


def test_raise_exception_invalid_executor():
    from jina.excepts import NoContainerizedError

    with pytest.raises(NoContainerizedError):
        f = Flow().add(uses='A')
        f.to_docker_compose_yaml()


def test_docker_compose_set_volume(tmpdir):
    default_workspace = __cache_path__

    custom_workspace = '/my/worki'
    custom_volume = 'my/cool:custom/volume'
    flow = (
        Flow(name='test-flow', port=9090)
        .add(uses='docker://image', name='executor0')
        .add(uses='docker://image', name='executor1', workspace=custom_workspace)
        .add(uses='docker://image', name='executor2', volumes=custom_volume)
    )

    dump_path = os.path.join(str(tmpdir), 'test_flow_docker_compose_volume.yml')

    flow.to_docker_compose_yaml(
        output_path=dump_path,
    )

    configuration = None
    with open(dump_path, encoding='utf-8') as f:
        configuration = yaml.safe_load(f)

    assert set(configuration.keys()) == {'version', 'services', 'networks'}
    assert configuration['version'] == '3.3'
    assert configuration['networks'] == {'jina-network': {'driver': 'bridge'}}
    services = configuration['services']
    assert (
        len(services) == 4
    )  # gateway, executor0-head, executor0, executor1-head, executor1, executor2-head, executor2
    assert set(services.keys()) == {
        'gateway',
        'executor0',
        'executor1',
        'executor2',
    }
    default_workspace_abspath = os.path.abspath(default_workspace)
    # check default volume and workspace
    assert services['executor0']['volumes'][0].startswith(default_workspace_abspath)
    assert services['executor0']['volumes'][0].endswith(':/app')
    assert '--workspace' in services['executor0']['command']
    wsp_index = services['executor0']['command'].index('--workspace') + 1
    assert services['executor0']['command'][wsp_index] == '/app/' + os.path.relpath(
        path=default_workspace, start=Path.home()
    )

    # check default volume, but respect custom workspace
    assert services['executor1']['volumes'][0].startswith(default_workspace_abspath)
    assert services['executor1']['volumes'][0].endswith(':/app')
    assert '--workspace' in services['executor1']['command']
    wsp_index = services['executor1']['command'].index('--workspace') + 1
    assert services['executor1']['command'][wsp_index] == custom_workspace

    # check custom value respected, no workspace added
    assert services['executor2']['volumes'] == [custom_volume]
    assert 'workspace' not in services['executor2']['command']


def test_disable_auto_volume(tmpdir):
    flow = Flow(name='test-flow', port=9090).add(
        uses='docker://image', name='executor0', disable_auto_volume=True
    )

    dump_path = os.path.join(str(tmpdir), 'test_flow_docker_compose_volume.yml')

    flow.to_docker_compose_yaml(output_path=dump_path)

    configuration = None
    with open(dump_path, encoding='utf-8') as f:
        configuration = yaml.safe_load(f)

    assert set(configuration.keys()) == {'version', 'services', 'networks'}
    assert configuration['version'] == '3.3'
    assert configuration['networks'] == {'jina-network': {'driver': 'bridge'}}
    services = configuration['services']
    assert len(services) == 2  # gateway, executor0-head, executor0
    assert set(services.keys()) == {
        'gateway',
        'executor0',
    }
    assert 'volumes' not in services['executor0']


@pytest.mark.parametrize(
    'uses',
    ['jinaai+sandbox://jina-ai/DummyHubExecutor'],
)
def test_flow_to_docker_compose_sandbox(tmpdir, uses):
    flow = Flow(name='test-flow', port=8080).add(uses=uses)

    dump_path = os.path.join(str(tmpdir), 'test_flow_docker_compose.yml')

    flow.to_docker_compose_yaml(
        output_path=dump_path,
    )

    configuration = None
    with open(dump_path, encoding='utf-8') as f:
        configuration = yaml.safe_load(f)

    services = configuration['services']
    gateway_service = services['gateway']
    gateway_args = gateway_service['command']

    deployment_addresses = json.loads(
        gateway_args[gateway_args.index('--deployments-addresses') + 1]
    )
    assert deployment_addresses['executor0'][0].startswith('grpcs://')


@pytest.mark.parametrize('count', [1, 'all'])
def test_flow_to_docker_compose_gpus(tmpdir, count):
    flow = Flow().add(name='encoder', gpus=count)
    dump_path = os.path.join(str(tmpdir), 'test_flow_docker_compose_gpus.yml')

    flow.to_docker_compose_yaml(
        output_path=dump_path,
    )

    configuration = None
    with open(dump_path, encoding='utf-8') as f:
        configuration = yaml.safe_load(f)

    services = configuration['services']
    encoder_service = services['encoder']
    assert encoder_service['deploy'] == {
        'resources': {
            'reservations': {
                'devices': [
                    {'driver': 'nvidia', 'count': count, 'capabilities': ['gpu']}
                ]
            }
        }
    }
