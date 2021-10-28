import asyncio
import os

import docker
import pytest

from jina import Flow
from jina.peapods.networking import K8sGrpcConnectionPool
from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


@pytest.mark.asyncio
async def test_wait_for_ready(
    slow_init_executor_image, k8s_cluster, load_images_in_kind, set_test_pip_version
):
    flow = Flow(
        name='test-flow-slow-executor',
        infrastructure='K8S',
        timeout_ready=120000,
    ).add(
        name='slow_init_executor',
        uses=slow_init_executor_image,
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
        pool.close()
