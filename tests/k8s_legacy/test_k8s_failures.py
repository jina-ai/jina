import asyncio
import datetime
import functools
import os
import subprocess
import time
from typing import Set

import pytest
from pytest_kind import cluster

from jina import Document, Flow

cluster.KIND_VERSION = 'v0.11.1'

async def create_all_flow_deployments_and_wait_ready(
        flow_dump_path,
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

    deployment_set = set(os.listdir(flow_dump_path))
    for deployment_name in deployment_set:
        file_set = set(os.listdir(os.path.join(flow_dump_path, deployment_name)))
        for file in file_set:
            try:
                utils.create_from_yaml(
                    api_client,
                    yaml_file=os.path.join(flow_dump_path, deployment_name, file),
                    namespace=namespace,
                )
            except Exception as e:
                # some objects are not successfully created since they exist from previous files
                logger.info(
                    f'Did not create resource from {file} for pod {deployment_name} due to {e} '
                )
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
    resp2 = app_client.list_namespaced_stateful_set(namespace=namespace)
    deployment_names = set([item.metadata.name for item in resp.items])
    sset_names = set([item.metadata.name for item in resp2.items])
    all_execs_names = deployment_names.union(sset_names)
    assert all_execs_names == set(deployment_replicas_expected.keys())
    while len(all_execs_names) > 0:
        deployments_ready = []
        for deployment_name in all_execs_names:
            if deployment_name in deployment_names:
                api_response = app_client.read_namespaced_deployment(
                    name=deployment_name, namespace=namespace
                )
            elif deployment_name in sset_names:
                api_response = app_client.read_namespaced_stateful_set(
                    name=deployment_name, namespace=namespace
                )
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
            all_execs_names.remove(deployment_name)
        logger.info(f'Waiting for {all_execs_names} to be ready')
        await asyncio.sleep(1.0)

async def scale(
    deployment_name: str,
    desired_replicas: int,
    app_client,
    k8s_namespace,
    core_client,
    logger,
):
    app_client.patch_namespaced_deployment_scale(
        deployment_name,
        namespace=k8s_namespace,
        body={'spec': {'replicas': desired_replicas}},
    )
    # wait for replicas to be dead
    while True:
        pods = core_client.list_namespaced_pod(
            namespace=k8s_namespace,
            label_selector=f'app={deployment_name}',
        )
        if len(pods.items) == desired_replicas:
            # still continue for a bit to hit the new replica only
            logger.info(
                f'Scale {deployment_name} to {desired_replicas} replicas complete'
            )
            await asyncio.sleep(2.0)
            break
        logger.info(f'waiting for scaling of {deployment_name} to be complete')
        await asyncio.sleep(2.0)


async def restart_deployment(
    deployment, app_client, core_client, k8s_namespace, logger
):
    now = datetime.datetime.utcnow()
    now = str(now.isoformat("T") + "Z")
    body = {
        'spec': {
            'template': {
                'metadata': {'annotations': {'kubectl.kubernetes.io/restartedAt': now}}
            }
        }
    }

    pods = core_client.list_namespaced_pod(
        namespace=k8s_namespace,
        label_selector=f'app={deployment}',
    )
    old_pod_names = [p.metadata.name for p in pods.items]
    logger.info(f'Restart deployment {deployment}')
    app_client.patch_namespaced_deployment(
        deployment, k8s_namespace, body, pretty='true'
    )
    while True:
        pods = core_client.list_namespaced_pod(
            namespace=k8s_namespace,
            label_selector=f'app={deployment}',
        )
        current_pod_names = [p.metadata.name for p in pods.items]
        if not any(i in current_pod_names for i in old_pod_names):
            logger.info(f'All pods in deployment {deployment} have been restarted')
            break
        logger.info(f'Waiting for all pods in deployment {deployment} to be restarted')
        await asyncio.sleep(2.0)


async def delete_pod(deployment, core_client, k8s_namespace, logger):
    pods = core_client.list_namespaced_pod(
        namespace=k8s_namespace,
        label_selector=f'app={deployment}',
    )
    api_response = core_client.delete_namespaced_pod(
        pods.items[0].metadata.name, k8s_namespace
    )
    while True:
        current_pods = core_client.list_namespaced_pod(
            namespace=k8s_namespace,
            label_selector=f'app={deployment}',
        )
        current_pod_names = [p.metadata.name for p in current_pods.items]
        if pods.items[0].metadata.name not in current_pod_names:
            logger.info(
                f'Pod {pods.items[0].metadata.name} in deployment {deployment} has been deleted'
            )
            while True:
                current_pods = core_client.list_namespaced_pod(
                    namespace=k8s_namespace,
                    label_selector=f'app={deployment}',
                )
                if len(current_pods.items) == len(pods.items):
                    logger.info(
                        f'All pods in deployment {deployment} are ready after deleting a Pod'
                    )
                    return
                logger.info(
                    f'Waiting for {len(current_pods.items)} pods in deployment {deployment} to be ready after deleting a Pod'
                )
                await asyncio.sleep(2.0)
        logger.info(
            f'Waiting for pod {pods.items[0].metadata.name} in deployment {deployment} to be deleted'
        )
        await asyncio.sleep(2.0)


async def run_test_until_event(
    flow, core_client, namespace, endpoint, stop_event, logger, sleep_time=0.05
):
    # start port forwarding
    from jina.clients import Client

    gateway_pod_name = (
        core_client.list_namespaced_pod(
            namespace=namespace, label_selector='app=gateway'
        )
        .items[0]
        .metadata.name
    )
    config_path = os.environ['KUBECONFIG']
    import portforward

    with portforward.forward(
        namespace, gateway_pod_name, flow.port, flow.port, config_path
    ):
        client_kwargs = dict(
            host='localhost',
            port=flow.port,
            asyncio=True,
        )
        client_kwargs.update(flow._common_kwargs)

        client = Client(**client_kwargs)
        client.show_progress = True

        async def async_inputs(sent_ids: Set[int], sleep_time: float = 0.05):
            i = 0
            while True:
                sent_ids.add(i)
                yield Document(text=f'{i}')
                if stop_event.is_set():
                    logger.info(f'stop yielding new requests after {i} requests')
                    return
                elif sleep_time:
                    await asyncio.sleep(sleep_time)
                i += 1

        responses = []
        sent_ids = set()
        async for resp in client.post(
            endpoint,
            inputs=functools.partial(async_inputs, sent_ids, sleep_time),
            request_size=1,
            return_responses=True
        ):
            responses.append(resp)

    logger.info(
        f'Client sent {len(sent_ids)} and received {(len(responses))} responses'
    )
    return responses, sent_ids


def inject_failures(k8s_cluster, logger):
    k8s_cluster.install_linkderd_smi()
    logger.info(f'Inject random failures into test cluster')
    proc = subprocess.Popen(
        [
            str(k8s_cluster._cluster.kubectl_path),
            'apply',
            '-f',
            './tests/k8s/fault-inject.yml',
        ],
        env={"KUBECONFIG": str(k8s_cluster._kube_config_path)},
    )
    returncode = proc.poll()
    logger.info(
        f'Injecting failures into cluster ended with returned code {returncode}'
    )
    if returncode is not None and returncode != 0:
        raise Exception(f"Injecting failures failed with {returncode}")


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['set-text-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_failure_scenarios(logger, docker_images, tmpdir, k8s_cluster):
    namespace = 'test-failure-scenarios'
    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)

    flow = Flow(prefetch=100).add(replicas=3, uses=f'docker://{docker_images[0]}')

    dump_path = os.path.join(str(tmpdir), namespace)
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'executor0': 3,
        },
        logger=logger,
    )
    stop_event = asyncio.Event()
    send_task = asyncio.create_task(
        run_test_until_event(
            flow=flow,
            namespace=namespace,
            core_client=core_client,
            endpoint='/',
            stop_event=stop_event,
            logger=logger,
            sleep_time=None,
        )
    )
    await asyncio.sleep(5.0)
    # Scale down the Executor to 2 replicas
    await scale(
        deployment_name='executor0',
        desired_replicas=2,
        core_client=core_client,
        app_client=app_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    # Scale back up to 3 replicas
    await scale(
        deployment_name='executor0',
        desired_replicas=3,
        core_client=core_client,
        app_client=app_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    await asyncio.sleep(5.0)
    # restart all pods in the deployment
    await restart_deployment(
        deployment='executor0',
        app_client=app_client,
        core_client=core_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    await asyncio.sleep(5.0)
    await delete_pod(
        deployment='executor0',
        core_client=core_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    await asyncio.sleep(5.0)

    stop_event.set()
    responses, sent_ids = await send_task
    assert len(sent_ids) == len(responses)
    doc_ids = set()
    pod_ids = set()
    for response in responses:
        doc_id, pod_id = response.docs.texts[0].split('_')
        doc_ids.add(doc_id)
        pod_ids.add(pod_id)
    assert len(sent_ids) == len(doc_ids)
    assert len(pod_ids) == 8  # 3 original + 3 restarted + 1 scaled up + 1 deleted

    # do the random failure test
    # start sending again
    logger.info('Start sending for random failure test')
    stop_event.clear()
    send_task = asyncio.create_task(
        run_test_until_event(
            flow=flow,
            namespace=namespace,
            core_client=core_client,
            endpoint='/',
            stop_event=stop_event,
            logger=logger,
        )
    )
    # inject failures
    inject_failures(k8s_cluster, logger)
    # wait a bit
    await asyncio.sleep(3.0)
    # check that no message was lost
    stop_event.set()
    responses, sent_ids = await send_task
    assert len(sent_ids) == len(responses)
