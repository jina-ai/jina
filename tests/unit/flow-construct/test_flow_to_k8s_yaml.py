import os
import yaml

import pytest

from jina import Flow


@pytest.mark.parametrize('k8s_connection_pool', [False, True])
@pytest.mark.parametrize('protocol', ['http', 'grpc'])
def test_flow_to_k8s_yaml(tmpdir, protocol, k8s_connection_pool):
    flow = (
        Flow(name='test-flow', port_expose=8080, protocol=protocol)
        .add(name='executor0', uses_with={'param': 0})
        .add(name='executor1', shards=2, uses_with={'param': 0})
        .add(
            name='executor2',
            uses_before='docker://image',
            uses_after='docker://image',
            uses_with={'param': 0},
        )
    )

    dump_path = os.path.join(str(tmpdir), 'test_flow_k8s')

    namespace = 'test-flow-ns'
    flow.to_k8s_yaml(
        output_base_path=dump_path,
        k8s_namespace=namespace,
        k8s_connection_pool=k8s_connection_pool,
    )
    assert set(os.listdir(dump_path)) == {
        'executor0',
        'executor1',
        'executor2',
        'gateway',
    }
    assert set(os.listdir(os.path.join(dump_path, 'gateway'))) == {'gateway.yml'}
    assert set(os.listdir(os.path.join(dump_path, 'executor0'))) == {
        'executor0-head-0.yml',
        'executor0.yml',
    }
    assert set(os.listdir(os.path.join(dump_path, 'executor1'))) == {
        'executor1-head-0.yml',
        'executor1-0.yml',
        'executor1-1.yml',
    }
    assert set(os.listdir(os.path.join(dump_path, 'executor2'))) == {
        'executor2-head-0.yml',
        'executor2.yml',
    }
    yaml_dicts_per_deployment = {
        'gateway': [],
        'executor0': [],
        'executor0-head-0': [],
        'executor1-head-0': [],
        'executor1-0': [],
        'executor1-1': [],
        'executor2-head-0': [],
        'executor2': [],
    }
    for pod_name in set(os.listdir(dump_path)):
        file_set = set(os.listdir(os.path.join(dump_path, pod_name)))
        for file in file_set:
            with open(os.path.join(dump_path, pod_name, file)) as f:
                yml_document_all = list(yaml.safe_load_all(f))
            yaml_dicts_per_deployment[file[:-4]] = yml_document_all

    gateway_objects = yaml_dicts_per_deployment['gateway']
    assert (
        len(gateway_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert gateway_objects[0]['kind'] == 'Role'
    assert gateway_objects[0]['metadata']['namespace'] == namespace
    assert gateway_objects[0]['metadata']['name'] == 'connection-pool'

    assert gateway_objects[1]['kind'] == 'RoleBinding'
    assert gateway_objects[1]['metadata']['namespace'] == namespace
    assert gateway_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert gateway_objects[2]['kind'] == 'ConfigMap'
    assert gateway_objects[2]['metadata']['namespace'] == namespace
    assert gateway_objects[2]['metadata']['name'] == 'gateway-configmap'

    assert gateway_objects[3]['kind'] == 'Service'
    assert gateway_objects[3]['metadata']['namespace'] == namespace
    assert gateway_objects[3]['metadata']['labels']['app'] == 'gateway'
    assert gateway_objects[3]['metadata']['name'] == 'gateway'

    assert gateway_objects[4]['kind'] == 'Deployment'
    assert gateway_objects[4]['metadata']['namespace'] == namespace
    assert gateway_objects[4]['metadata']['name'] == 'gateway'
    assert gateway_objects[4]['spec']['replicas'] == 1
    gateway_args = gateway_objects[4]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert gateway_args[0] == 'gateway'
    assert '--port-in' in gateway_args
    assert gateway_args[gateway_args.index('--port-in') + 1] == '8081'
    assert '--port-expose' in gateway_args
    assert gateway_args[gateway_args.index('--port-expose') + 1] == '8080'
    assert '--k8s-namespace' in gateway_args
    assert gateway_args[gateway_args.index('--k8s-namespace') + 1] == namespace
    assert '--graph-description' in gateway_args
    assert (
        gateway_args[gateway_args.index('--graph-description') + 1]
        == '{"executor0": ["executor1"], "start-gateway": ["executor0"], "executor1": ["executor2"], "executor2": ["end-gateway"]}'
    )
    if k8s_connection_pool is False:
        assert '--pods-addresses' in gateway_args
        assert (
            gateway_args[gateway_args.index('--pods-addresses') + 1]
            == '{"executor0": ["executor0-head-0.test-flow-ns.svc:8081"], "executor1": ["executor1-head-0.test-flow-ns.svc:8081"], "executor2": ["executor2-head-0.test-flow-ns.svc:8081"]}'
        )
    assert '--pea-role' in gateway_args
    assert gateway_args[gateway_args.index('--pea-role') + 1] == 'GATEWAY'
    if protocol == 'http':
        assert '--protocol' in gateway_args
        assert gateway_args[gateway_args.index('--protocol') + 1] == 'HTTP'
    else:
        assert '--protocol' not in gateway_args
    assert '--uses-with' not in gateway_args

    executor0_head0_objects = yaml_dicts_per_deployment['executor0-head-0']
    assert (
        len(executor0_head0_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert executor0_head0_objects[0]['kind'] == 'Role'
    assert executor0_head0_objects[0]['metadata']['namespace'] == namespace
    assert executor0_head0_objects[0]['metadata']['name'] == 'connection-pool'

    assert executor0_head0_objects[1]['kind'] == 'RoleBinding'
    assert executor0_head0_objects[1]['metadata']['namespace'] == namespace
    assert executor0_head0_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert executor0_head0_objects[2]['kind'] == 'ConfigMap'
    assert executor0_head0_objects[2]['metadata']['namespace'] == namespace
    assert (
        executor0_head0_objects[2]['metadata']['name'] == 'executor0-head-0-configmap'
    )

    assert executor0_head0_objects[3]['kind'] == 'Service'
    assert executor0_head0_objects[3]['metadata']['namespace'] == namespace
    assert executor0_head0_objects[3]['metadata']['labels']['app'] == 'executor0-head-0'
    assert executor0_head0_objects[3]['metadata']['name'] == 'executor0-head-0'

    assert executor0_head0_objects[4]['kind'] == 'Deployment'
    assert executor0_head0_objects[4]['metadata']['namespace'] == namespace
    assert executor0_head0_objects[4]['metadata']['name'] == 'executor0-head-0'
    assert executor0_head0_objects[4]['spec']['replicas'] == 1
    executor0_head0_args = executor0_head0_objects[4]['spec']['template']['spec'][
        'containers'
    ][0]['args']
    assert executor0_head0_args[0] == 'executor'
    assert '--name' in executor0_head0_args
    assert (
        executor0_head0_args[executor0_head0_args.index('--name') + 1]
        == 'executor0/head-0'
    )
    assert '--k8s-namespace' in executor0_head0_args
    assert (
        executor0_head0_args[executor0_head0_args.index('--k8s-namespace') + 1]
        == namespace
    )
    assert '--runtime-cls' in executor0_head0_args
    assert (
        executor0_head0_args[executor0_head0_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pea-role' in executor0_head0_args
    assert executor0_head0_args[executor0_head0_args.index('--pea-role') + 1] == 'HEAD'
    assert '--native' in executor0_head0_args
    if not k8s_connection_pool:
        assert '--k8s-disable-connection-pool' in executor0_head0_args
        assert '--connection-list' in executor0_head0_args
        assert (
            executor0_head0_args[executor0_head0_args.index('--connection-list') + 1]
            == '{"0": "executor0.test-flow-ns.svc:8081"}'
        )
    else:
        assert '--k8s-disable-connection-pool' not in executor0_head0_args
        assert '--connection-list' not in executor0_head0_args
    assert '--uses-with' not in executor0_head0_args

    executor0_objects = yaml_dicts_per_deployment['executor0']
    assert (
        len(executor0_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert executor0_objects[0]['kind'] == 'Role'
    assert executor0_objects[0]['metadata']['namespace'] == namespace
    assert executor0_objects[0]['metadata']['name'] == 'connection-pool'

    assert executor0_objects[1]['kind'] == 'RoleBinding'
    assert executor0_objects[1]['metadata']['namespace'] == namespace
    assert executor0_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert executor0_objects[2]['kind'] == 'ConfigMap'
    assert executor0_objects[2]['metadata']['namespace'] == namespace
    assert executor0_objects[2]['metadata']['name'] == 'executor0-configmap'

    assert executor0_objects[3]['kind'] == 'Service'
    assert executor0_objects[3]['metadata']['namespace'] == namespace
    assert executor0_objects[3]['metadata']['labels']['app'] == 'executor0'
    assert executor0_objects[3]['metadata']['name'] == 'executor0'

    assert executor0_objects[4]['kind'] == 'Deployment'
    assert executor0_objects[4]['metadata']['namespace'] == namespace
    assert executor0_objects[4]['metadata']['name'] == 'executor0'
    assert executor0_objects[4]['spec']['replicas'] == 1
    executor0_args = executor0_objects[4]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert executor0_args[0] == 'executor'
    assert '--name' in executor0_args
    assert executor0_args[executor0_args.index('--name') + 1] == 'executor0'
    assert '--k8s-namespace' in executor0_args
    assert executor0_args[executor0_args.index('--k8s-namespace') + 1] == namespace
    assert '--uses-with' in executor0_args
    assert executor0_args[executor0_args.index('--uses-with') + 1] == '{"param": 0}'
    assert '--uses-metas' in executor0_args
    assert executor0_args[executor0_args.index('--uses-metas') + 1] == '{"pea_id": 0}'
    assert '--native' in executor0_args
    assert '--k8s-disable-connection-pool' not in executor0_args
    assert '--pea-role' not in executor0_args
    assert '--runtime-cls' not in executor0_args
    assert '--connection-list' not in executor0_args

    executor1_head0_objects = yaml_dicts_per_deployment['executor1-head-0']
    assert (
        len(executor1_head0_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert executor1_head0_objects[0]['kind'] == 'Role'
    assert executor1_head0_objects[0]['metadata']['namespace'] == namespace
    assert executor1_head0_objects[0]['metadata']['name'] == 'connection-pool'

    assert executor1_head0_objects[1]['kind'] == 'RoleBinding'
    assert executor1_head0_objects[1]['metadata']['namespace'] == namespace
    assert executor1_head0_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert executor1_head0_objects[2]['kind'] == 'ConfigMap'
    assert executor1_head0_objects[2]['metadata']['namespace'] == namespace
    assert (
        executor1_head0_objects[2]['metadata']['name'] == 'executor1-head-0-configmap'
    )

    assert executor1_head0_objects[3]['kind'] == 'Service'
    assert executor1_head0_objects[3]['metadata']['namespace'] == namespace
    assert executor1_head0_objects[3]['metadata']['labels']['app'] == 'executor1-head-0'
    assert executor1_head0_objects[3]['metadata']['name'] == 'executor1-head-0'

    assert executor1_head0_objects[4]['kind'] == 'Deployment'
    assert executor1_head0_objects[4]['metadata']['namespace'] == namespace
    assert executor1_head0_objects[4]['metadata']['name'] == 'executor1-head-0'
    assert executor1_head0_objects[4]['spec']['replicas'] == 1
    executor1_head0_args = executor1_head0_objects[4]['spec']['template']['spec'][
        'containers'
    ][0]['args']
    assert executor1_head0_args[0] == 'executor'
    assert '--name' in executor1_head0_args
    assert (
        executor1_head0_args[executor1_head0_args.index('--name') + 1]
        == 'executor1/head-0'
    )
    assert '--k8s-namespace' in executor1_head0_args
    assert (
        executor1_head0_args[executor1_head0_args.index('--k8s-namespace') + 1]
        == namespace
    )
    assert '--runtime-cls' in executor1_head0_args
    assert (
        executor1_head0_args[executor1_head0_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pea-role' in executor1_head0_args
    assert executor1_head0_args[executor1_head0_args.index('--pea-role') + 1] == 'HEAD'
    assert '--native' in executor1_head0_args
    if not k8s_connection_pool:
        assert '--k8s-disable-connection-pool' in executor1_head0_args
        assert '--connection-list' in executor1_head0_args
        assert (
            executor1_head0_args[executor1_head0_args.index('--connection-list') + 1]
            == '{"0": "executor1-0.test-flow-ns.svc:8081", "1": "executor1-1.test-flow-ns.svc:8081"}'
        )
    else:
        assert '--k8s-disable-connection-pool' not in executor1_head0_args
        assert '--connection-list' not in executor1_head0_args
    assert '--uses-with' not in executor1_head0_args

    executor1_shard0_objects = yaml_dicts_per_deployment['executor1-0']
    assert (
        len(executor1_shard0_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert executor1_shard0_objects[0]['kind'] == 'Role'
    assert executor1_shard0_objects[0]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[0]['metadata']['name'] == 'connection-pool'

    assert executor1_shard0_objects[1]['kind'] == 'RoleBinding'
    assert executor1_shard0_objects[1]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert executor1_shard0_objects[2]['kind'] == 'ConfigMap'
    assert executor1_shard0_objects[2]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[2]['metadata']['name'] == 'executor1-0-configmap'

    assert executor1_shard0_objects[3]['kind'] == 'Service'
    assert executor1_shard0_objects[3]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[3]['metadata']['labels']['app'] == 'executor1-0'
    assert executor1_shard0_objects[3]['metadata']['name'] == 'executor1-0'

    assert executor1_shard0_objects[4]['kind'] == 'Deployment'
    assert executor1_shard0_objects[4]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[4]['metadata']['name'] == 'executor1-0'
    assert executor1_shard0_objects[4]['spec']['replicas'] == 1
    executor1_shard0_args = executor1_shard0_objects[4]['spec']['template']['spec'][
        'containers'
    ][0]['args']
    assert executor1_shard0_args[0] == 'executor'
    assert '--name' in executor1_shard0_args
    assert (
        executor1_shard0_args[executor1_shard0_args.index('--name') + 1]
        == 'executor1-0'
    )
    assert '--k8s-namespace' in executor1_shard0_args
    assert (
        executor1_shard0_args[executor1_shard0_args.index('--k8s-namespace') + 1]
        == namespace
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
    assert '--k8s-disable-connection-pool' not in executor1_shard0_args
    assert '--pea-role' not in executor1_shard0_args
    assert '--runtime-cls' not in executor1_shard0_args
    assert '--connection-list' not in executor1_shard0_args

    executor1_shard1_objects = yaml_dicts_per_deployment['executor1-1']
    assert (
        len(executor1_shard1_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert executor1_shard1_objects[0]['kind'] == 'Role'
    assert executor1_shard1_objects[0]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[0]['metadata']['name'] == 'connection-pool'

    assert executor1_shard1_objects[1]['kind'] == 'RoleBinding'
    assert executor1_shard1_objects[1]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert executor1_shard1_objects[2]['kind'] == 'ConfigMap'
    assert executor1_shard1_objects[2]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[2]['metadata']['name'] == 'executor1-1-configmap'

    assert executor1_shard1_objects[3]['kind'] == 'Service'
    assert executor1_shard1_objects[3]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[3]['metadata']['labels']['app'] == 'executor1-1'
    assert executor1_shard1_objects[3]['metadata']['name'] == 'executor1-1'

    assert executor1_shard1_objects[4]['kind'] == 'Deployment'
    assert executor1_shard1_objects[4]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[4]['metadata']['name'] == 'executor1-1'
    assert executor1_shard1_objects[4]['spec']['replicas'] == 1
    executor1_shard1_args = executor1_shard1_objects[4]['spec']['template']['spec'][
        'containers'
    ][0]['args']
    assert executor1_shard1_args[0] == 'executor'
    assert '--name' in executor1_shard1_args
    assert (
        executor1_shard1_args[executor1_shard1_args.index('--name') + 1]
        == 'executor1-1'
    )
    assert '--k8s-namespace' in executor1_shard1_args
    assert (
        executor1_shard1_args[executor1_shard1_args.index('--k8s-namespace') + 1]
        == namespace
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
    assert '--k8s-disable-connection-pool' not in executor1_shard1_args
    assert '--pea-role' not in executor1_shard1_args
    assert '--runtime-cls' not in executor1_shard1_args
    assert '--connection-list' not in executor1_shard1_args

    executor2_head0_objects = yaml_dicts_per_deployment['executor2-head-0']
    assert (
        len(executor2_head0_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert executor2_head0_objects[0]['kind'] == 'Role'
    assert executor2_head0_objects[0]['metadata']['namespace'] == namespace
    assert executor2_head0_objects[0]['metadata']['name'] == 'connection-pool'

    assert executor2_head0_objects[1]['kind'] == 'RoleBinding'
    assert executor2_head0_objects[1]['metadata']['namespace'] == namespace
    assert executor2_head0_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert executor2_head0_objects[2]['kind'] == 'ConfigMap'
    assert executor2_head0_objects[2]['metadata']['namespace'] == namespace
    assert (
        executor2_head0_objects[2]['metadata']['name'] == 'executor2-head-0-configmap'
    )

    assert executor2_head0_objects[3]['kind'] == 'Service'
    assert executor2_head0_objects[3]['metadata']['namespace'] == namespace
    assert executor2_head0_objects[3]['metadata']['labels']['app'] == 'executor2-head-0'
    assert executor2_head0_objects[3]['metadata']['name'] == 'executor2-head-0'

    assert executor2_head0_objects[4]['kind'] == 'Deployment'
    assert executor2_head0_objects[4]['metadata']['namespace'] == namespace
    assert executor2_head0_objects[4]['metadata']['name'] == 'executor2-head-0'
    assert executor2_head0_objects[4]['spec']['replicas'] == 1
    executor2_head_containers = executor2_head0_objects[4]['spec']['template']['spec'][
        'containers'
    ]
    assert len(executor2_head_containers) == 3  # head, uses_before, uses_after
    executor2_head0_args = executor2_head_containers[0]['args']
    assert executor2_head0_args[0] == 'executor'
    assert '--name' in executor2_head0_args
    assert (
        executor2_head0_args[executor2_head0_args.index('--name') + 1]
        == 'executor2/head-0'
    )
    assert '--k8s-namespace' in executor2_head0_args
    assert (
        executor2_head0_args[executor2_head0_args.index('--k8s-namespace') + 1]
        == namespace
    )
    assert '--runtime-cls' in executor2_head0_args
    assert (
        executor2_head0_args[executor2_head0_args.index('--runtime-cls') + 1]
        == 'HeadRuntime'
    )
    assert '--pea-role' in executor2_head0_args
    assert executor2_head0_args[executor2_head0_args.index('--pea-role') + 1] == 'HEAD'
    assert '--native' in executor2_head0_args
    if not k8s_connection_pool:
        assert '--k8s-disable-connection-pool' in executor2_head0_args
        assert '--connection-list' in executor2_head0_args
        assert (
            executor2_head0_args[executor2_head0_args.index('--connection-list') + 1]
            == '{"0": "executor2.test-flow-ns.svc:8081"}'
        )
    else:
        assert '--k8s-disable-connection-pool' not in executor2_head0_args
        assert '--connection-list' not in executor2_head0_args
    assert '--uses-with' not in executor2_head0_args

    executor2_uses_before_args = executor2_head_containers[1]['args']
    assert executor2_uses_before_args[0] == 'executor'
    assert '--name' in executor2_uses_before_args
    assert (
        executor2_uses_before_args[executor2_uses_before_args.index('--name') + 1]
        == 'executor2/uses-before'
    )
    assert '--k8s-namespace' in executor2_uses_before_args
    assert (
        executor2_uses_before_args[
            executor2_uses_before_args.index('--k8s-namespace') + 1
        ]
        == namespace
    )
    assert '--uses-with' not in executor2_uses_before_args
    assert '--uses-metas' in executor2_uses_before_args
    assert (
        executor2_uses_before_args[executor2_uses_before_args.index('--uses-metas') + 1]
        == '{}'
    )
    assert '--native' in executor2_uses_before_args
    assert '--k8s-disable-connection-pool' not in executor2_uses_before_args
    assert '--pea-role' not in executor2_uses_before_args
    assert '--runtime-cls' not in executor2_uses_before_args
    assert '--connection-list' not in executor2_uses_before_args

    executor2_uses_after_args = executor2_head_containers[2]['args']
    assert executor2_uses_after_args[0] == 'executor'
    assert '--name' in executor2_uses_after_args
    assert (
        executor2_uses_after_args[executor2_uses_after_args.index('--name') + 1]
        == 'executor2/uses-after'
    )
    assert '--k8s-namespace' in executor2_uses_after_args
    assert (
        executor2_uses_after_args[
            executor2_uses_after_args.index('--k8s-namespace') + 1
        ]
        == namespace
    )
    assert '--uses-with' not in executor2_uses_after_args
    assert '--uses-metas' in executor2_uses_after_args
    assert (
        executor2_uses_after_args[executor2_uses_after_args.index('--uses-metas') + 1]
        == '{}'
    )
    assert '--native' in executor2_uses_after_args
    assert '--k8s-disable-connection-pool' not in executor2_uses_after_args
    assert '--pea-role' not in executor2_uses_after_args
    assert '--runtime-cls' not in executor2_uses_after_args
    assert '--connection-list' not in executor2_uses_after_args

    executor2_objects = yaml_dicts_per_deployment['executor2']
    assert (
        len(executor2_objects) == 5
    )  # role, role-binding, config-map, service, deployment
    assert executor2_objects[0]['kind'] == 'Role'
    assert executor2_objects[0]['metadata']['namespace'] == namespace
    assert executor0_objects[0]['metadata']['name'] == 'connection-pool'

    assert executor2_objects[1]['kind'] == 'RoleBinding'
    assert executor2_objects[1]['metadata']['namespace'] == namespace
    assert executor2_objects[1]['metadata']['name'] == 'connection-pool-binding'

    assert executor2_objects[2]['kind'] == 'ConfigMap'
    assert executor2_objects[2]['metadata']['namespace'] == namespace
    assert executor2_objects[2]['metadata']['name'] == 'executor2-configmap'

    assert executor2_objects[3]['kind'] == 'Service'
    assert executor2_objects[3]['metadata']['namespace'] == namespace
    assert executor2_objects[3]['metadata']['labels']['app'] == 'executor2'
    assert executor2_objects[3]['metadata']['name'] == 'executor2'

    assert executor2_objects[4]['kind'] == 'Deployment'
    assert executor2_objects[4]['metadata']['namespace'] == namespace
    assert executor2_objects[4]['metadata']['name'] == 'executor2'
    assert executor2_objects[4]['spec']['replicas'] == 1
    executor2_args = executor2_objects[4]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert executor2_args[0] == 'executor'
    assert '--name' in executor2_args
    assert executor2_args[executor2_args.index('--name') + 1] == 'executor2'
    assert '--k8s-namespace' in executor2_args
    assert executor2_args[executor2_args.index('--k8s-namespace') + 1] == namespace
    assert '--uses-with' in executor2_args
    assert executor2_args[executor2_args.index('--uses-with') + 1] == '{"param": 0}'
    assert '--uses-metas' in executor2_args
    assert executor2_args[executor2_args.index('--uses-metas') + 1] == '{"pea_id": 0}'
    assert '--native' in executor2_args
    assert '--k8s-disable-connection-pool' not in executor2_args
    assert '--pea-role' not in executor2_args
    assert '--runtime-cls' not in executor2_args
    assert '--connection-list' not in executor2_args
