import os

import pytest
import requests as req

from jina import Flow
from jina.serve.networking import GrpcConnectionPool
from tests.k8s_legacy.util import create_all_flow_deployments_and_wait_ready

@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
async def test_flow_with_monitoring(logger, tmpdir, docker_images, port_generator):
    try:
        dump_path = os.path.join(str(tmpdir), 'test-flow-with-monitoring')
        namespace = f'test-flow-monitoring'.lower()

        flow = Flow(name='test-flow-monitoring', monitoring=True).add(
            name='segmenter',
            uses=f'docker://{docker_images[0]}',
        )

        flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

        from kubernetes import client

        api_client = client.ApiClient()
        core_client = client.CoreV1Api(api_client=api_client)
        app_client = client.AppsV1Api(api_client=api_client)
        await create_all_flow_deployments_and_wait_ready(
            dump_path,
            namespace=namespace,
            api_client=api_client,
            app_client=app_client,
            core_client=core_client,
            deployment_replicas_expected={
                'gateway': 1,
                'segmenter': 1,
            },
            logger=logger,
        )
        import portforward

        config_path = os.environ['KUBECONFIG']
        gateway_pod_name = (
            core_client.list_namespaced_pod(
                namespace=namespace, label_selector='app=gateway'
            )
                .items[0]
                .metadata.name
        )

        executor_pod_name = (
            core_client.list_namespaced_pod(
                namespace=namespace, label_selector='app=segmenter'
            )
                .items[0]
                .metadata.name
        )

        port_monitoring = GrpcConnectionPool.K8S_PORT_MONITORING
        port = port_generator()

        for pod_name in [gateway_pod_name, executor_pod_name]:
            with portforward.forward(
                    namespace, pod_name, port, port_monitoring, config_path
            ):
                resp = req.get(f'http://localhost:{port}/')
                assert resp.status_code == 200

        core_client.delete_namespace(namespace)
    except Exception as exc:
        logger.error(f' Exception raised {exc}')
        raise exc