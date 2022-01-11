import asyncio
import os

import pytest

from jina.peapods.networking import K8sGrpcConnectionPool

cur_dir = os.path.dirname(__file__)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images',
    [['jinaai/jina'], ['test-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_process_up_down_events(docker_images):
    from kubernetes import client
    from kubernetes import utils

    k8s_client = client.ApiClient()
    app_client = client.AppsV1Api(api_client=k8s_client)
    core_client = client.CoreV1Api(api_client=k8s_client)
    namespace = f'pool-test-namespace-{docker_images[0][0:4]}'
    namespace_object = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {'name': f'{namespace}'},
    }
    try:
        utils.create_from_dict(k8s_client, namespace_object)
    except:
        pass
    container_args = ['executor', '--native', '--port-in', '8081']
    if 'test-executor' in docker_images[0]:
        container_args.extend(['--uses', 'config.yml'])
    deployment_object = {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {'name': 'dummy-deployment', 'namespace': f'{namespace}'},
        'spec': {
            'replicas': 1,
            'strategy': {
                'type': 'RollingUpdate',
                'rollingUpdate': {'maxSurge': 1, 'maxUnavailable': 0},
            },
            'selector': {'matchLabels': {'app': 'dummy-deployment'}},
            'template': {
                'metadata': {
                    'labels': {
                        'app': 'dummy-deployment',
                        'jina_pod_name': 'some-pod',
                        'shard_id': '4',
                        'pea_type': 'WORKER',
                        'ns': f'{namespace}',
                    }
                },
                'spec': {
                    'containers': [
                        {
                            'name': 'executor',
                            'image': docker_images[0],
                            'command': ['jina'],
                            'args': container_args,
                            'ports': [{'containerPort': 8081}],
                            'readinessProbe': {
                                'tcpSocket': {'port': 8081},
                                'initialDelaySeconds': 5,
                                'periodSeconds': 10,
                            },
                        }
                    ]
                },
            },
        },
    }
    utils.create_from_dict(k8s_client, deployment_object, namespace=namespace)
    pool = K8sGrpcConnectionPool(namespace=namespace, client=core_client)
    pool.start()
    await asyncio.sleep(1.0)
    namespaced_pods = core_client.list_namespaced_pod(namespace)
    while not namespaced_pods.items:
        await asyncio.sleep(1.0)
        namespaced_pods = core_client.list_namespaced_pod(namespace)

    assigned_pod_ip = namespaced_pods.items[0].status.pod_ip
    for container in namespaced_pods.items[0].spec.containers:
        if container.name == 'executor':
            assigned_port = container.ports[0].container_port
            break

    expected_replicas = 1

    while True:
        api_response = app_client.read_namespaced_deployment(
            name='dummy-deployment', namespace=namespace
        )
        if (
            api_response.status.ready_replicas is not None
            and api_response.status.ready_replicas == expected_replicas
            or (api_response.status.ready_replicas is None and expected_replicas == 0)
        ):
            replica_lists = pool._connections.get_replicas_all_shards('some-pod')
            assert expected_replicas == sum(
                [
                    len(replica_list.get_all_connections())
                    for replica_list in replica_lists
                ]
            )

            if expected_replicas == 1:
                replica_lists[0].has_connection(f'{assigned_pod_ip}:{assigned_port}')
                # scale up to 2 replicas
                app_client.patch_namespaced_deployment_scale(
                    'dummy-deployment',
                    namespace=namespace,
                    body={'spec': {'replicas': 2}},
                )
                expected_replicas += 1
            elif expected_replicas == 2:
                # scale down by 2 replicas
                app_client.patch_namespaced_deployment_scale(
                    'dummy-deployment',
                    namespace=namespace,
                    body={'spec': {'replicas': 0}},
                )
                expected_replicas = 0
            else:
                break
        else:
            await asyncio.sleep(1.0)
    await pool.close()
