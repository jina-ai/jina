import json
import os

import pytest
import yaml

from jina import Flow
from jina.serve.networking import GrpcConnectionPool


@pytest.mark.parametrize('protocol', ['http', 'grpc'])
@pytest.mark.parametrize('flow_port', [1234, None])
@pytest.mark.parametrize('gateway_replicas', [1, 2])
def test_flow_to_k8s_yaml(tmpdir, protocol, flow_port, gateway_replicas):
    flow_kwargs = {'name': 'test-flow', 'protocol': protocol}
    gateway_kwargs = {'protocol': protocol}
    if flow_port:
        flow_kwargs['port'] = flow_port
        gateway_kwargs['port'] = flow_port
    gateway_kwargs['replicas'] = gateway_replicas
    gateway_kwargs['env_from_secret'] = {
        'SECRET_GATEWAY_USERNAME': {'name': 'gateway_secret', 'key': 'gateway_username'},
    }
    gateway_kwargs['image_pull_secrets'] = ['secret1', 'secret2']

    flow = (
        Flow(**flow_kwargs).config_gateway(**gateway_kwargs)
        .add(name='executor0', uses_with={'param': 0}, timeout_ready=60000)
        .add(
            name='executor1',
            shards=2,
            uses_with={'param': 0},
            env_from_secret={
                'SECRET_USERNAME': {'name': 'mysecret', 'key': 'username'},
                'SECRET_PASSWORD': {'name': 'mysecret', 'key': 'password'},
            },
            image_pull_secrets=['secret3', 'secret4']
        )
        .add(
            name='executor2',
            uses_before='docker://image',
            uses_after='docker://image',
            uses_with={'param': 0},
            shards=2,
        )
    )

    dump_path = os.path.join(str(tmpdir), 'test_flow_k8s')

    namespace = 'test-flow-ns'
    flow.to_kubernetes_yaml(
        output_base_path=dump_path,
        k8s_namespace=namespace,
    )
    assert set(os.listdir(dump_path)) == {
        'executor0',
        'executor1',
        'executor2',
        'gateway',
    }
    assert set(os.listdir(os.path.join(dump_path, 'gateway'))) == {'gateway.yml'}
    assert set(os.listdir(os.path.join(dump_path, 'executor0'))) == {
        'executor0.yml',
    }
    assert set(os.listdir(os.path.join(dump_path, 'executor1'))) == {
        'executor1-head.yml',
        'executor1-0.yml',
        'executor1-1.yml',
    }
    assert set(os.listdir(os.path.join(dump_path, 'executor2'))) == {
        'executor2-head.yml',
        'executor2-0.yml',
        'executor2-1.yml',
    }
    yaml_dicts_per_deployment = {
        'gateway': [],
        'executor0': [],
        'executor1-head': [],
        'executor1-0': [],
        'executor1-1': [],
        'executor2-head': [],
        'executor2-0': [],
        'executor2-1': [],
    }
    for pod_name in set(os.listdir(dump_path)):
        file_set = set(os.listdir(os.path.join(dump_path, pod_name)))
        for file in file_set:
            with open(os.path.join(dump_path, pod_name, file), encoding='utf-8') as f:
                yml_document_all = list(yaml.safe_load_all(f))
            yaml_dicts_per_deployment[file[:-4]] = yml_document_all

    gateway_objects = yaml_dicts_per_deployment['gateway']
    assert len(gateway_objects) == 3  # config-map, service, deployment
    assert gateway_objects[0]['kind'] == 'ConfigMap'
    assert gateway_objects[0]['metadata']['namespace'] == namespace
    assert gateway_objects[0]['metadata']['name'] == 'gateway-configmap'

    assert gateway_objects[1]['kind'] == 'Service'
    assert gateway_objects[2]['metadata']['namespace'] == namespace
    assert gateway_objects[1]['metadata']['labels']['app'] == 'gateway'
    assert gateway_objects[1]['metadata']['name'] == 'gateway'

    assert gateway_objects[2]['kind'] == 'Deployment'
    assert gateway_objects[2]['metadata']['namespace'] == namespace
    assert gateway_objects[2]['metadata']['name'] == 'gateway'
    assert gateway_objects[2]['spec']['replicas'] == gateway_replicas
    assert gateway_objects[2]['spec']['template']['spec']['ImagePullSecrets'] == [{'name': 'secret1'}, {'name': 'secret2'}]

    gateway_args = gateway_objects[2]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert gateway_args[0] == 'gateway'
    assert '--port' in gateway_args
    assert gateway_args[gateway_args.index('--port') + 1] == (
        str(flow_port) if flow_port else str(GrpcConnectionPool.K8S_PORT)
    )
    assert gateway_args[gateway_args.index('--port') + 1] == str(flow.port)
    assert '--k8s-namespace' in gateway_args
    assert gateway_args[gateway_args.index('--k8s-namespace') + 1] == namespace
    assert '--graph-description' in gateway_args
    assert (
        gateway_args[gateway_args.index('--graph-description') + 1]
        == '{"executor0": ["executor1"], "start-gateway": ["executor0"], "executor1": ["executor2"], "executor2": ["end-gateway"]}'
    )
    assert '--deployments-addresses' in gateway_args
    assert (
        gateway_args[gateway_args.index('--deployments-addresses') + 1]
        == '{"executor0": ["grpc://executor0.test-flow-ns.svc:8080"], "executor1": ["grpc://executor1-head.test-flow-ns.svc:8080"], "executor2": ["grpc://executor2-head.test-flow-ns.svc:8080"]}'
    )
    if protocol == 'http':
        assert '--protocol' in gateway_args
        assert gateway_args[gateway_args.index('--protocol') + 1] == 'HTTP'
    else:
        assert '--protocol' not in gateway_args
    assert '--uses-with' not in gateway_args
    gateway_env = gateway_objects[2]['spec']['template']['spec']['containers'][0]['env']
    assert gateway_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'gateway'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'gateway'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
        {
            'name': 'SECRET_GATEWAY_USERNAME',
            'valueFrom': {'secretKeyRef': {'name': 'gateway_secret', 'key': 'gateway_username'}},
        },
    ]

    executor0_objects = yaml_dicts_per_deployment['executor0']
    assert len(executor0_objects) == 3  # config-map, service, deployment

    assert executor0_objects[0]['kind'] == 'ConfigMap'
    assert executor0_objects[0]['metadata']['namespace'] == namespace
    assert executor0_objects[0]['metadata']['name'] == 'executor0-configmap'

    assert executor0_objects[1]['kind'] == 'Service'
    assert executor0_objects[1]['metadata']['namespace'] == namespace
    assert executor0_objects[1]['metadata']['labels']['app'] == 'executor0'
    assert executor0_objects[1]['metadata']['name'] == 'executor0'

    assert executor0_objects[2]['kind'] == 'Deployment'
    assert executor0_objects[2]['metadata']['namespace'] == namespace
    assert executor0_objects[2]['metadata']['name'] == 'executor0'
    assert executor0_objects[2]['spec']['replicas'] == 1

    executor0_startup_probe = executor0_objects[2]['spec']['template']['spec'][
        'containers'
    ][0]['startupProbe']
    assert executor0_startup_probe['failureThreshold'] == 12
    assert executor0_startup_probe['periodSeconds'] == 5

    executor0_args = executor0_objects[2]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert executor0_args[0] == 'executor'
    assert '--name' in executor0_args
    assert executor0_args[executor0_args.index('--name') + 1] == 'executor0'
    assert '--k8s-namespace' in executor0_args
    assert executor0_args[executor0_args.index('--k8s-namespace') + 1] == namespace
    assert '--uses-with' in executor0_args
    assert executor0_args[executor0_args.index('--uses-with') + 1] == '{"param": 0}'
    assert '--native' in executor0_args
    assert '--pod-role' not in executor0_args
    assert '--runtime-cls' not in executor0_args
    assert '--connection-list' not in executor0_args
    executor0_env = executor0_objects[2]['spec']['template']['spec']['containers'][0][
        'env'
    ]
    assert executor0_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor0'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor0'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
    ]

    executor1_head0_objects = yaml_dicts_per_deployment['executor1-head']
    assert len(executor1_head0_objects) == 3  # config-map, service, deployment
    assert executor1_head0_objects[0]['kind'] == 'ConfigMap'
    assert executor1_head0_objects[0]['metadata']['namespace'] == namespace
    assert executor1_head0_objects[0]['metadata']['name'] == 'executor1-head-configmap'

    assert executor1_head0_objects[1]['kind'] == 'Service'
    assert executor1_head0_objects[1]['metadata']['namespace'] == namespace
    assert executor1_head0_objects[1]['metadata']['labels']['app'] == 'executor1-head'
    assert executor1_head0_objects[1]['metadata']['name'] == 'executor1-head'

    assert executor1_head0_objects[2]['kind'] == 'Deployment'
    assert executor1_head0_objects[2]['metadata']['namespace'] == namespace
    assert executor1_head0_objects[2]['metadata']['name'] == 'executor1-head'
    assert executor1_head0_objects[2]['spec']['replicas'] == 1
    assert executor1_head0_objects[2]['spec']['template']['spec']['ImagePullSecrets'] == [{'name': 'secret3'}, {'name': 'secret4'}]
    executor1_head0_args = executor1_head0_objects[2]['spec']['template']['spec'][
        'containers'
    ][0]['args']
    assert executor1_head0_args[0] == 'executor'
    assert '--name' in executor1_head0_args
    assert (
        executor1_head0_args[executor1_head0_args.index('--name') + 1]
        == 'executor1/head'
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
    assert '--pod-role' in executor1_head0_args
    assert executor1_head0_args[executor1_head0_args.index('--pod-role') + 1] == 'HEAD'
    assert '--native' in executor1_head0_args

    assert '--connection-list' in executor1_head0_args
    assert (
        executor1_head0_args[executor1_head0_args.index('--connection-list') + 1]
        == '{"0": "executor1-0.test-flow-ns.svc:8080", "1": "executor1-1.test-flow-ns.svc:8080"}'
    )

    assert '--uses-with' not in executor1_head0_args
    executor1_head0_env = executor1_head0_objects[2]['spec']['template']['spec'][
        'containers'
    ][0]['env']
    assert executor1_head0_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor1'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor1-head'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
        {
            'name': 'SECRET_USERNAME',
            'valueFrom': {'secretKeyRef': {'name': 'mysecret', 'key': 'username'}},
        },
        {
            'name': 'SECRET_PASSWORD',
            'valueFrom': {'secretKeyRef': {'name': 'mysecret', 'key': 'password'}},
        },
    ]

    executor1_shard0_objects = yaml_dicts_per_deployment['executor1-0']
    assert len(executor1_shard0_objects) == 3  # config-map, service, deployment

    assert executor1_shard0_objects[0]['kind'] == 'ConfigMap'
    assert executor1_shard0_objects[0]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[0]['metadata']['name'] == 'executor1-0-configmap'

    assert executor1_shard0_objects[1]['kind'] == 'Service'
    assert executor1_shard0_objects[1]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[1]['metadata']['labels']['app'] == 'executor1-0'
    assert executor1_shard0_objects[1]['metadata']['name'] == 'executor1-0'

    assert executor1_shard0_objects[2]['kind'] == 'Deployment'
    assert executor1_shard0_objects[2]['metadata']['namespace'] == namespace
    assert executor1_shard0_objects[2]['metadata']['name'] == 'executor1-0'
    assert executor1_shard0_objects[2]['spec']['replicas'] == 1
    assert executor1_shard0_objects[2]['spec']['template']['spec']['ImagePullSecrets'] == [{'name': 'secret3'}, {'name': 'secret4'}]
    executor1_shard0_args = executor1_shard0_objects[2]['spec']['template']['spec'][
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
    assert '--native' in executor1_shard0_args
    assert '--pod-role' not in executor1_shard0_args
    assert '--runtime-cls' not in executor1_shard0_args
    assert '--connection-list' not in executor1_shard0_args
    executor1_shard0_env = executor1_shard0_objects[2]['spec']['template']['spec'][
        'containers'
    ][0]['env']
    assert executor1_shard0_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor1'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor1-0'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
        {
            'name': 'SECRET_USERNAME',
            'valueFrom': {'secretKeyRef': {'name': 'mysecret', 'key': 'username'}},
        },
        {
            'name': 'SECRET_PASSWORD',
            'valueFrom': {'secretKeyRef': {'name': 'mysecret', 'key': 'password'}},
        },
    ]

    executor1_shard1_objects = yaml_dicts_per_deployment['executor1-1']
    assert len(executor1_shard1_objects) == 3  # config-map, service, deployment

    assert executor1_shard1_objects[0]['kind'] == 'ConfigMap'
    assert executor1_shard1_objects[0]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[0]['metadata']['name'] == 'executor1-1-configmap'

    assert executor1_shard1_objects[1]['kind'] == 'Service'
    assert executor1_shard1_objects[1]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[1]['metadata']['labels']['app'] == 'executor1-1'
    assert executor1_shard1_objects[1]['metadata']['name'] == 'executor1-1'

    assert executor1_shard1_objects[2]['kind'] == 'Deployment'
    assert executor1_shard1_objects[2]['metadata']['namespace'] == namespace
    assert executor1_shard1_objects[2]['metadata']['name'] == 'executor1-1'
    assert executor1_shard1_objects[2]['spec']['replicas'] == 1
    assert executor1_shard1_objects[2]['spec']['template']['spec']['ImagePullSecrets'] == [{'name': 'secret3'}, {'name': 'secret4'}]
    executor1_shard1_args = executor1_shard1_objects[2]['spec']['template']['spec'][
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
    assert '--native' in executor1_shard1_args
    assert '--pod-role' not in executor1_shard1_args
    assert '--runtime-cls' not in executor1_shard1_args
    assert '--connection-list' not in executor1_shard1_args
    executor1_shard1_env = executor1_shard1_objects[2]['spec']['template']['spec'][
        'containers'
    ][0]['env']
    assert executor1_shard1_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor1'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor1-1'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
        {
            'name': 'SECRET_USERNAME',
            'valueFrom': {'secretKeyRef': {'name': 'mysecret', 'key': 'username'}},
        },
        {
            'name': 'SECRET_PASSWORD',
            'valueFrom': {'secretKeyRef': {'name': 'mysecret', 'key': 'password'}},
        },
    ]

    executor2_head0_objects = yaml_dicts_per_deployment['executor2-head']
    assert len(executor2_head0_objects) == 3  # config-map, service, deployment

    assert executor2_head0_objects[0]['kind'] == 'ConfigMap'
    assert executor2_head0_objects[0]['metadata']['namespace'] == namespace
    assert executor2_head0_objects[0]['metadata']['name'] == 'executor2-head-configmap'

    assert executor2_head0_objects[1]['kind'] == 'Service'
    assert executor2_head0_objects[1]['metadata']['namespace'] == namespace
    assert executor2_head0_objects[1]['metadata']['labels']['app'] == 'executor2-head'
    assert executor2_head0_objects[1]['metadata']['name'] == 'executor2-head'

    assert executor2_head0_objects[2]['kind'] == 'Deployment'
    assert executor2_head0_objects[2]['metadata']['namespace'] == namespace
    assert executor2_head0_objects[2]['metadata']['name'] == 'executor2-head'
    assert executor2_head0_objects[2]['spec']['replicas'] == 1
    executor2_head_containers = executor2_head0_objects[2]['spec']['template']['spec'][
        'containers'
    ]
    assert len(executor2_head_containers) == 3  # head, uses_before, uses_after
    executor2_head0_args = executor2_head_containers[0]['args']
    assert executor2_head0_args[0] == 'executor'
    assert '--name' in executor2_head0_args
    assert (
        executor2_head0_args[executor2_head0_args.index('--name') + 1]
        == 'executor2/head'
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
    assert '--pod-role' in executor2_head0_args
    assert executor2_head0_args[executor2_head0_args.index('--pod-role') + 1] == 'HEAD'
    assert '--native' in executor2_head0_args
    assert '--connection-list' in executor2_head0_args
    assert (
        executor2_head0_args[executor2_head0_args.index('--connection-list') + 1]
        == '{"0": "executor2-0.test-flow-ns.svc:8080", "1": "executor2-1.test-flow-ns.svc:8080"}'
    )
    assert '--uses-with' not in executor2_head0_args
    executor2_head0_env = executor2_head_containers[0]['env']
    assert executor2_head0_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor2'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor2-head'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
    ]

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
    assert '--pod-role' not in executor2_uses_before_args
    assert '--runtime-cls' not in executor2_uses_before_args
    assert '--connection-list' not in executor2_uses_before_args
    executor2_uses_before_env = executor2_head_containers[1]['env']
    assert executor2_uses_before_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor2'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor2-head'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
    ]

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
    assert '--pod-role' not in executor2_uses_after_args
    assert '--runtime-cls' not in executor2_uses_after_args
    assert '--connection-list' not in executor2_uses_after_args
    executor2_uses_after_env = executor2_head_containers[2]['env']
    assert executor2_uses_after_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor2'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor2-head'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
    ]

    executor2_objects = yaml_dicts_per_deployment['executor2-0']
    assert len(executor2_objects) == 3  # config-map, service, deployment

    assert executor2_objects[0]['kind'] == 'ConfigMap'
    assert executor2_objects[0]['metadata']['namespace'] == namespace
    assert executor2_objects[0]['metadata']['name'] == 'executor2-0-configmap'

    assert executor2_objects[1]['kind'] == 'Service'
    assert executor2_objects[1]['metadata']['namespace'] == namespace
    assert executor2_objects[1]['metadata']['labels']['app'] == 'executor2-0'
    assert executor2_objects[1]['metadata']['name'] == 'executor2-0'

    assert executor2_objects[2]['kind'] == 'Deployment'
    assert executor2_objects[2]['metadata']['namespace'] == namespace
    assert executor2_objects[2]['metadata']['name'] == 'executor2-0'
    assert executor2_objects[2]['spec']['replicas'] == 1
    executor2_args = executor2_objects[2]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert executor2_args[0] == 'executor'
    assert '--name' in executor2_args
    assert executor2_args[executor2_args.index('--name') + 1] == 'executor2-0'
    assert '--k8s-namespace' in executor2_args
    assert executor2_args[executor2_args.index('--k8s-namespace') + 1] == namespace
    assert '--uses-with' in executor2_args
    assert executor2_args[executor2_args.index('--uses-with') + 1] == '{"param": 0}'
    assert '--native' in executor2_args
    assert '--pod-role' not in executor2_args
    assert '--runtime-cls' not in executor2_args
    assert '--connection-list' not in executor2_args
    executor2_env = executor2_objects[2]['spec']['template']['spec']['containers'][0][
        'env'
    ]
    assert executor2_env == [
        {'name': 'POD_UID', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.uid'}}},
        {'name': 'JINA_DEPLOYMENT_NAME', 'value': 'executor2'},
        {'name': 'K8S_DEPLOYMENT_NAME', 'value': 'executor2-0'},
        {'name': 'K8S_NAMESPACE_NAME', 'value': namespace},
        {
            'name': 'K8S_POD_NAME',
            'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}},
        },
    ]


@pytest.mark.parametrize('has_external', [False, True])
def test_flow_to_k8s_yaml_external_pod(tmpdir, has_external):

    flow = Flow(name='test-flow', port=8080).add(
        name='executor0',
    )

    if has_external:
        flow = flow.add(
            name='external_executor', external=True, host='1.2.3.4', port=9090
        )
    else:
        flow = flow.add(name='external_executor')

    dump_path = os.path.join(str(tmpdir), 'test_flow_k8s')

    namespace = 'test-flow-ns'
    flow.to_kubernetes_yaml(
        output_base_path=dump_path,
        k8s_namespace=namespace,
    )

    yaml_dicts_per_deployment = {
        'gateway': [],
        'executor0': [],
    }
    assert len(set(os.listdir(dump_path))) == 2 if has_external else 3
    for pod_name in set(os.listdir(dump_path)):
        file_set = set(os.listdir(os.path.join(dump_path, pod_name)))
        for file in file_set:
            with open(os.path.join(dump_path, pod_name, file), encoding='utf-8') as f:
                yml_document_all = list(yaml.safe_load_all(f))
            yaml_dicts_per_deployment[file[:-4]] = yml_document_all

    gateway_objects = yaml_dicts_per_deployment['gateway']
    gateway_args = gateway_objects[2]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert (
        gateway_args[gateway_args.index('--graph-description') + 1]
        == '{"executor0": ["external_executor"], "start-gateway": ["executor0"], "external_executor": ["end-gateway"]}'
    )

    if has_external:
        assert '--deployments-addresses' in gateway_args
        assert (
            gateway_args[gateway_args.index('--deployments-addresses') + 1]
            == '{"executor0": ["grpc://executor0.test-flow-ns.svc:8080"], "external_executor": ["grpc://1.2.3.4:9090"]}'
        )
    else:
        assert '--deployments-addresses' in gateway_args
        assert (
            gateway_args[gateway_args.index('--deployments-addresses') + 1]
            == '{"executor0": ["grpc://executor0.test-flow-ns.svc:8080"], "external_executor": ["grpc://external-executor.test-flow-ns.svc:8080"]}'
        )


def test_raise_exception_invalid_executor(tmpdir):
    from jina.excepts import NoContainerizedError

    with pytest.raises(NoContainerizedError):
        f = Flow().add(uses='A')
        f.to_kubernetes_yaml(str(tmpdir))


@pytest.mark.parametrize(
    'uses',
    [
        f'jinaai+sandbox://jina-ai/DummyHubExecutor',
    ],
)
def test_flow_to_k8s_yaml_sandbox(tmpdir, uses):

    flow = Flow(name='test-flow', port=8080).add(uses=uses)

    dump_path = os.path.join(str(tmpdir), 'test_flow_k8s')

    namespace = 'test-flow-ns'
    flow.to_kubernetes_yaml(
        output_base_path=dump_path,
        k8s_namespace=namespace,
    )

    yaml_dicts_per_deployment = {
        'gateway': [],
    }
    for pod_name in set(os.listdir(dump_path)):
        file_set = set(os.listdir(os.path.join(dump_path, pod_name)))
        for file in file_set:
            with open(os.path.join(dump_path, pod_name, file), encoding='utf-8') as f:
                yml_document_all = list(yaml.safe_load_all(f))
            yaml_dicts_per_deployment[file[:-4]] = yml_document_all

    gateway_objects = yaml_dicts_per_deployment['gateway']
    gateway_args = gateway_objects[2]['spec']['template']['spec']['containers'][0][
        'args'
    ]
    assert (
        gateway_args[gateway_args.index('--graph-description') + 1]
        == '{"executor0": ["end-gateway"], "start-gateway": ["executor0"]}'
    )

    assert '--deployments-addresses' in gateway_args
    deployment_addresses = json.loads(
        gateway_args[gateway_args.index('--deployments-addresses') + 1]
    )
    assert deployment_addresses['executor0'][0].startswith('grpcs://')
