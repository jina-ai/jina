import os
import yaml

import pytest

from jina import Flow


@pytest.mark.parametrize('protocol', ['http', 'grpc'])
def test_flow_to_docker_compose_yaml(tmpdir, protocol):
    flow = (
        Flow(name='test-flow', port_in=9090, port_expose=8080, protocol=protocol)
        .add(name='executor0', uses_with={'param': 0})
        .add(name='executor1', shards=2, uses_with={'param': 0})
        .add(
            replicas=2,
            name='executor2',
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
    with open(dump_path) as f:
        configuration = yaml.safe_load(f)

    assert set(configuration.keys()) == {'version', 'services', 'networks'}
    assert configuration['version'] == '3.3'
    assert configuration['networks'] == {'jina-network': {'driver': 'bridge'}}
    services = configuration['services']
    assert (
        len(services) == 11
    )  # gateway, executor0-head, executor0, executor1-head, executor1-0, executor1-1,
    # executor2-head, executor2-rep-0, executor2-rep-1, executor2-uses-before, executor2-uses-after
    assert set(services.keys()) == {
        'gateway',
        'executor0-head-0',
        'executor0',
        'executor1-head-0',
        'executor1-0',
        'executor1-1',
        'executor2-head-0',
        'executor2-rep-0',
        'executor2-rep-1',
        'executor2-uses-before',
        'executor2-uses-after',
    }

    gateway_service = services['gateway']
    assert gateway_service['entrypoint'] == ['jina']
    assert gateway_service['expose'] == ['8080', '9090']
    assert gateway_service['ports'] == ['8080:8080', '9090:9090']
    gateway_args = gateway_service['command']
    assert gateway_args[0] == 'gateway'
    assert '--port-in' in gateway_args
    assert gateway_args[gateway_args.index('--port-in') + 1] == '9090'
    assert '--port-expose' in gateway_args
    assert gateway_args[gateway_args.index('--port-expose') + 1] == '8080'
    assert '--graph-description' in gateway_args
    assert (
        gateway_args[gateway_args.index('--graph-description') + 1]
        == '{"executor0": ["executor1"], "start-gateway": ["executor0"], "executor1": ["executor2"], "executor2": ["end-gateway"]}'
    )
    assert '--pods-addresses' in gateway_args
    assert (
        gateway_args[gateway_args.index('--pods-addresses') + 1]
        == '{"executor0": ["executor0-head-0:8081"], "executor1": ["executor1-head-0:8081"], "executor2": ["executor2-head-0:8081"]}'
    )
    assert '--pea-role' in gateway_args
    assert gateway_args[gateway_args.index('--pea-role') + 1] == 'GATEWAY'
    if protocol == 'http':
        assert '--protocol' in gateway_args
        assert gateway_args[gateway_args.index('--protocol') + 1] == 'HTTP'
    else:
        assert '--protocol' not in gateway_args
    assert '--uses-with' not in gateway_args
    assert '--env' not in gateway_args

    executor0_head_service = services['executor0-head-0']
    assert executor0_head_service['entrypoint'] == ['jina']
    assert 'expose' not in executor0_head_service
    executor0_head_args = executor0_head_service['command']
    assert executor0_head_args[0] == 'executor'
    assert '--name' in executor0_head_args
    assert (
        executor0_head_args[executor0_head_args.index('--name') + 1]
        == 'executor0/head-0'
    )
    assert '--runtime-cls' in executor0_head_args
    assert (
        executor0_head_args[executor0_head_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pea-role' in executor0_head_args
    assert executor0_head_args[executor0_head_args.index('--pea-role') + 1] == 'HEAD'
    assert '--native' in executor0_head_args
    assert '--connection-list' in executor0_head_args
    assert (
        executor0_head_args[executor0_head_args.index('--connection-list') + 1]
        == '{"0": ["executor0:8081"]}'
    )
    assert '--uses-with' not in executor0_head_args
    assert '--uses-before' not in executor0_head_args
    assert '--uses-after' not in executor0_head_args
    assert '--envs' not in executor0_head_args
    assert '--uses-before-address' not in executor0_head_args
    assert '--uses-after-address' not in executor0_head_args

    executor0_service = services['executor0']
    assert executor0_service['entrypoint'] == ['jina']
    assert 'expose' not in executor0_service
    executor0_args = executor0_service['command']
    assert '--replica-id' in executor0_args
    assert executor0_args[executor0_args.index('--replica-id') + 1] == '-1'
    assert executor0_args[0] == 'executor'
    assert '--name' in executor0_args
    assert executor0_args[executor0_args.index('--name') + 1] == 'executor0'
    assert '--uses-with' in executor0_args
    assert executor0_args[executor0_args.index('--uses-with') + 1] == '{"param": 0}'
    assert '--uses-metas' in executor0_args
    assert executor0_args[executor0_args.index('--uses-metas') + 1] == '{"pea_id": 0}'
    assert '--native' in executor0_args
    assert '--pea-role' not in executor0_args
    assert '--runtime-cls' not in executor0_args
    assert '--connection-list' not in executor0_args
    assert '--uses-before' not in executor0_args
    assert '--uses-after' not in executor0_args

    executor1_head_service = services['executor1-head-0']
    assert executor1_head_service['entrypoint'] == ['jina']
    assert 'expose' not in executor1_head_service
    executor1_head_args = executor1_head_service['command']
    assert executor1_head_args[0] == 'executor'
    assert '--name' in executor1_head_args
    assert (
        executor1_head_args[executor1_head_args.index('--name') + 1]
        == 'executor1/head-0'
    )
    assert '--runtime-cls' in executor1_head_args
    assert (
        executor1_head_args[executor1_head_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pea-role' in executor1_head_args
    assert executor1_head_args[executor1_head_args.index('--pea-role') + 1] == 'HEAD'
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
    assert '--replica-id' in executor1_shard0_args
    assert (
        executor1_shard0_args[executor1_shard0_args.index('--replica-id') + 1] == '-1'
    )
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
    assert (
        executor1_shard0_args[executor1_shard0_args.index('--uses-metas') + 1]
        == '{"pea_id": 0}'
    )
    assert '--native' in executor1_shard0_args
    assert '--pea-role' not in executor1_shard0_args
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
    assert '--replica-id' in executor1_shard1_args
    assert (
        executor1_shard1_args[executor1_shard1_args.index('--replica-id') + 1] == '-1'
    )
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
    assert (
        executor1_shard1_args[executor1_shard1_args.index('--uses-metas') + 1]
        == '{"pea_id": 1}'
    )
    assert '--native' in executor1_shard1_args
    assert '--pea-role' not in executor1_shard1_args
    assert '--runtime-cls' not in executor1_shard1_args
    assert '--connection-list' not in executor1_shard1_args
    assert '--uses-before' not in executor1_shard1_args
    assert '--uses-after' not in executor1_shard1_args

    executor2_head_service = services['executor2-head-0']
    assert executor2_head_service['entrypoint'] == ['jina']
    assert 'expose' not in executor2_head_service
    executor2_head_args = executor2_head_service['command']
    assert executor2_head_args[0] == 'executor'
    assert '--name' in executor2_head_args
    assert (
        executor2_head_args[executor2_head_args.index('--name') + 1]
        == 'executor2/head-0'
    )
    assert '--runtime-cls' in executor2_head_args
    assert (
        executor2_head_args[executor2_head_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pea-role' in executor2_head_args
    assert executor2_head_args[executor2_head_args.index('--pea-role') + 1] == 'HEAD'
    assert '--native' in executor2_head_args
    assert '--connection-list' in executor2_head_args
    assert (
        executor2_head_args[executor2_head_args.index('--connection-list') + 1]
        == '{"0": ["executor2-rep-0:8081", "executor2-rep-1:8081"]}'
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

    executor2_rep_0_service = services['executor2-rep-0']
    assert executor2_rep_0_service['entrypoint'] == ['jina']
    assert 'expose' not in executor2_rep_0_service
    executor2_rep_0_args = executor2_rep_0_service['command']
    assert executor2_rep_0_args[0] == 'executor'
    assert '--name' in executor2_rep_0_args
    assert (
        executor2_rep_0_args[executor2_rep_0_args.index('--name') + 1]
        == 'executor2/rep-0'
    )
    assert '--uses-with' in executor2_rep_0_args
    assert (
        executor2_rep_0_args[executor2_rep_0_args.index('--uses-with') + 1]
        == '{"param": 0}'
    )
    assert '--uses-metas' in executor2_rep_0_args
    assert (
        executor2_rep_0_args[executor2_rep_0_args.index('--uses-metas') + 1]
        == '{"pea_id": 0}'
    )
    assert '--native' in executor2_rep_0_args
    assert '--pea-role' not in executor2_rep_0_args
    assert '--runtime-cls' not in executor2_rep_0_args
    assert '--connection-list' not in executor2_rep_0_args
    assert '--uses-before' not in executor2_rep_0_args
    assert '--uses-after' not in executor2_rep_0_args

    executor2_rep_1_service = services['executor2-rep-1']
    assert executor2_rep_1_service['entrypoint'] == ['jina']
    assert 'expose' not in executor2_rep_1_service
    executor2_rep_1_args = executor2_rep_1_service['command']
    assert executor2_rep_1_args[0] == 'executor'
    assert '--name' in executor2_rep_1_args
    assert (
        executor2_rep_1_args[executor2_rep_1_args.index('--name') + 1]
        == 'executor2/rep-1'
    )
    assert '--uses-with' in executor2_rep_1_args
    assert (
        executor2_rep_1_args[executor2_rep_1_args.index('--uses-with') + 1]
        == '{"param": 0}'
    )
    assert '--uses-metas' in executor2_rep_1_args
    assert (
        executor2_rep_1_args[executor2_rep_1_args.index('--uses-metas') + 1]
        == '{"pea_id": 0}'
    )
    assert '--replica-id' in executor2_rep_1_args
    assert executor2_rep_1_args[executor2_rep_1_args.index('--replica-id') + 1] == '1'
    assert '--native' in executor2_rep_1_args
    assert '--pea-role' not in executor2_rep_1_args
    assert '--runtime-cls' not in executor2_rep_1_args
    assert '--connection-list' not in executor2_rep_1_args
    assert '--uses-before' not in executor2_rep_1_args
    assert '--uses-after' not in executor2_rep_1_args

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
    assert '--pea-role' not in executor2_uses_before_args
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
    assert '--pea-role' not in executor2_uses_after_args
    assert '--runtime-cls' not in executor2_uses_after_args
    assert '--connection-list' not in executor2_uses_after_args
    assert '--uses-before' not in executor2_uses_after_args
    assert '--uses-after' not in executor2_uses_after_args
