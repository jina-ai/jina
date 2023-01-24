import asyncio
import os

import pytest
from docarray import DocumentArray
from pytest_kind import cluster

from jina import Deployment
from tests.k8s.conftest import shell_portforward

cluster.KIND_VERSION = 'v0.11.1'


async def create_executor_deployment_and_wait_ready(
    deployment_dump_path,
    namespace,
    api_client,
    app_client,
    core_client,
    deployment_replicas_expected,
    logger,
):
    from kubernetes import utils

    namespace = namespace.lower()
    namespace_object = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {'name': f'{namespace}'},
    }
    try:
        logger.info(f'create Namespace {namespace}')
        utils.create_from_dict(api_client, namespace_object)
    except:
        pass

    while True:
        ns_items = core_client.list_namespace().items
        if any(item.metadata.name == namespace for item in ns_items):
            logger.info(f'created Namespace {namespace}')
            break
        logger.info(f'waiting for Namespace {namespace}')
        await asyncio.sleep(1.0)

    file_set = set(os.listdir(deployment_dump_path))
    for file in file_set:
        try:
            utils.create_from_yaml(
                api_client,
                yaml_file=os.path.join(deployment_dump_path, file),
                namespace=namespace,
            )
        except Exception as e:
            # some objects are not successfully created since they exist from previous files
            logger.info(f'Did not create resource from {file} for pod due to {e} ')
            pass

    # wait for all the pods to be up
    expected_deployments = sum(deployment_replicas_expected.values())
    while True:
        namespaced_pods = core_client.list_namespaced_pod(namespace)
        if (
            namespaced_pods.items is not None
            and len(namespaced_pods.items) == expected_deployments
        ):
            break
        logger.info(
            f'Waiting for all {expected_deployments} Deployments to be created, only got {len(namespaced_pods.items) if namespaced_pods.items is not None else None}'
        )
        await asyncio.sleep(1.0)

    # wait for all the pods to be up
    resp = app_client.list_namespaced_deployment(namespace=namespace)
    deployment_names = set([item.metadata.name for item in resp.items])
    while len(deployment_names) > 0:
        deployments_ready = []
        for deployment_name in deployment_names:
            api_response = app_client.read_namespaced_deployment(
                name=deployment_name, namespace=namespace
            )
            print('api_response.status:', api_response.status)
            print('namespaced events:', core_client.list_namespaced_event(namespace))

            expected_num_replicas = deployment_replicas_expected[deployment_name]
            if (
                api_response.status.ready_replicas is not None
                and api_response.status.ready_replicas == expected_num_replicas
            ):
                logger.info(f'Deployment {deployment_name} is now ready')
                deployments_ready.append(deployment_name)
            else:
                logger.info(
                    f'Deployment {deployment_name} is not ready yet: ready_replicas is {api_response.status.ready_replicas} not equal to {expected_num_replicas}'
                )

        for deployment_name in deployments_ready:
            deployment_names.remove(deployment_name)
        logger.info(f'Waiting for {deployment_names} to be ready')
        await asyncio.sleep(1.0)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor']],
    indirect=True,
)
async def test_deployment_serve_k8s(logger, docker_images, tmpdir, k8s_cluster):
    from kubernetes import client

    namespace = 'test-deployment-serve-k8s'
    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)

    # test with custom port
    port = 12345
    try:
        dep = Deployment(
            name='test-executor',
            uses=f'docker://{docker_images[0]}',
            replicas=3,
            port=port,
        )

        dump_path = os.path.join(str(tmpdir), 'test-deployment-serve-k8s')
        dep.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

        await create_executor_deployment_and_wait_ready(
            dump_path,
            namespace=namespace,
            api_client=api_client,
            app_client=app_client,
            core_client=core_client,
            deployment_replicas_expected={
                'test-executor': 3,
            },
            logger=logger,
        )
        # start port forwarding
        from jina.clients import Client

        with shell_portforward(
            k8s_cluster._cluster.kubectl_path,
            'svc/test-executor',
            port,
            port,
            namespace,
        ):
            client = Client(port=port, asyncio=True)
            async for docs in client.post(
                '/debug', inputs=DocumentArray.empty(3), stream=False
            ):
                for doc in docs:
                    assert doc.tags['shards'] == 1
                    assert doc.tags['parallel'] == 3

    except Exception as exc:
        logger.error(f' Exception raised {exc}')
        raise exc
