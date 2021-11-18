import asyncio
import os

import docker
import pytest

from jina import Flow
from jina.peapods.networking import K8sGrpcConnectionPool
from jina.peapods.pods.k8slib import kubernetes_tools, kubernetes_deployment
from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


@pytest.mark.asyncio
async def test_process_up_down_events(
    alpine_image, k8s_cluster, load_images_in_kind, logger, test_dir: str
):
    namespace = 'pool-test-namespace'

    kubernetes_tools.create(
        'namespace',
        {'name': namespace},
    )
    custom_resource_dir = os.path.join(test_dir, 'custom-resource')
    kubernetes_deployment.deploy_service(
        name='dummy-deployment',
        namespace=namespace,
        image_name=alpine_image,
        container_cmd='["tail"]',
        container_args='["-f", "/dev/null"]',
        logger=logger,
        replicas=1,
        pull_policy='IfNotPresent',
        jina_pod_name='some-pod',
        pea_type='worker',
        custom_resource_dir=custom_resource_dir,
    )

    k8s_clients = K8sClients()
    pool = K8sGrpcConnectionPool(
        namespace=namespace,
        client=k8s_clients.core_v1,
    )
    pool.start()

    namespaced_pods = k8s_clients.core_v1.list_namespaced_pod(namespace)
    assigned_pod_ip = namespaced_pods.items[0].status.pod_ip
    for container in namespaced_pods.items[0].spec.containers:
        if container.name == 'executor':
            assigned_port = container.ports[0].container_port
            break

    expected_replicas = 1

    while True:
        api_response = k8s_clients.apps_v1.read_namespaced_deployment(
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
                k8s_clients.apps_v1.patch_namespaced_deployment_scale(
                    'dummy-deployment',
                    namespace=namespace,
                    body={"spec": {"replicas": 2}},
                )
                expected_replicas += 1
            elif expected_replicas == 2:
                # scale down by 2 replicas
                k8s_clients.apps_v1.patch_namespaced_deployment_scale(
                    'dummy-deployment',
                    namespace=namespace,
                    body={"spec": {"replicas": 0}},
                )
                expected_replicas = 0
            else:
                break
        else:
            await asyncio.sleep(1.0)
    await pool.close()


@pytest.mark.asyncio
async def test_wait_for_ready(
    k8s_cluster,
    image_name_tag_map,
):
    image_names = ['slow-init-executor']
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    flow = Flow(
        name='test-flow-slow-executor',
        infrastructure='K8S',
        timeout_ready=120000,
    ).add(
        name='slow_init_executor',
        uses=images[0],
        timeout_ready=360000,
    )

    with flow:
        k8s_clients = K8sClients()
        pool = K8sGrpcConnectionPool(
            namespace='test-flow-slow-executor',
            client=k8s_clients.core_v1,
        )
        pool.start()

        # pool should have connection to gateway and the one pod
        assert len(pool._connections) == 2
        for cluster_ip in pool._connections:
            # k8s pod has one instance at the moment
            assert len(pool._connections[cluster_ip]._connections) == 1

        # scale slow init executor up
        k8s_clients.apps_v1.patch_namespaced_deployment_scale(
            'slow-init-executor',
            namespace='test-flow-slow-executor',
            body={"spec": {"replicas": 2}},
        )

        while True:
            api_response = k8s_clients.apps_v1.read_namespaced_deployment(
                name='slow-init-executor', namespace='test-flow-slow-executor'
            )
            if (
                api_response.status.ready_replicas is not None
                and api_response.status.ready_replicas == 2
            ):
                # new replica is ready, check that connection pool knows about it
                slow_executor_connections = pool._connections[
                    pool._deployment_clusteraddresses['slow-init-executor']
                ]
                assert len(slow_executor_connections._connections) == 2
                break
            else:
                # new replica is not ready yet, make sure connection pool ignores it
                slow_executor_connections = pool._connections[
                    pool._deployment_clusteraddresses['slow-init-executor']
                ]
                assert len(slow_executor_connections._connections) == 1
            await asyncio.sleep(1.0)
        await pool.close()
