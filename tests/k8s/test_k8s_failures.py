import asyncio
import datetime
import functools
import multiprocessing
import os
import subprocess
from contextlib import suppress
from typing import Set

import pytest
from pytest_kind import cluster

from jina import Document, Flow
from tests.k8s.test_k8s_flow import create_all_flow_deployments_and_wait_ready

cluster.KIND_VERSION = 'v0.11.1'


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
    _ = core_client.delete_namespaced_pod(pods.items[0].metadata.name, k8s_namespace)

    while True:
        current_pods = core_client.list_namespaced_pod(
            namespace=k8s_namespace,
            label_selector=f'app={deployment}',
        )
        current_pod_names = [p.metadata.name for p in current_pods.items]
        logger.info(
            f'Deleted pod {pods.items[0].metadata.name} vs current pods {current_pod_names}'
        )
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
                    logger.info(
                        f'Pods {[item.metadata.name for item in pods.items]} vs Current pods {[item.metadata.name for item in current_pods.items]}'
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

    responses = []
    sent_ids = set()
    pod_ids = set()
    try:
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

            num_resps = 0
            async for resp in client.post(
                endpoint,
                inputs=functools.partial(async_inputs, sent_ids, sleep_time),
                request_size=1,
                return_responses=True,
                continue_on_error=True,
            ):
                num_resps += 1
                if resp.docs[0].tags['replica_uid'] not in pod_ids:
                    pod_ids.add(resp.docs[0].tags['replica_uid'])
                    logger.info(
                        f' Received response from a new POD UID {resp.docs[0].tags["replica_uid"]} => Now {len(pod_ids)} different `replicas` hit'
                    )
                responses.append(resp)
            logger.info(
                f'Stop sending requests after sending {len(sent_ids)} Documents and getting {num_resps} Responses'
            )
    except Exception as exc:
        logger.error(f' Exception raised in sending requests task: {exc}')
        # Let's also cancel all running tasks:
        logger.warning(f'Cancelling pending tasks and stopping the event loop.')
        loop = asyncio.get_event_loop()
        pending = asyncio.all_tasks()
        for task in pending:
            task.cancel()
            # Now we should await task to execute it's cancellation.
            # Cancelled task raises asyncio.CancelledError that we can suppress:
            with suppress(asyncio.CancelledError):
                loop.run_until_complete(task)

        logger.info(f'closing asycio event loop!')
        loop.close()

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
    namespace = 'test-failure-scenarios'.lower()
    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    flow = Flow(prefetch=100).add(replicas=2, uses=f'docker://{docker_images[0]}')

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
            'executor0': 2,
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
        )
    )
    logger.info(f' Sending task has been scheduled')
    await asyncio.sleep(5.0)
    # Scale down the Executor to 1 replicas
    await scale(
        deployment_name='executor0',
        desired_replicas=1,
        core_client=core_client,
        app_client=app_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    logger.info(f' Scaling to 1 replicas has been done')
    await asyncio.sleep(5.0)
    # Scale back up to 2 replicas
    await scale(
        deployment_name='executor0',
        desired_replicas=2,
        core_client=core_client,
        app_client=app_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    logger.info(f' Scaling to 2 replicas has been done')
    await asyncio.sleep(5.0)
    # restart all pods in the deployment
    await restart_deployment(
        deployment='executor0',
        app_client=app_client,
        core_client=core_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    logger.info(f' Restarting deployment has been done')
    await asyncio.sleep(5.0)
    await delete_pod(
        deployment='executor0',
        core_client=core_client,
        k8s_namespace=namespace,
        logger=logger,
    )
    logger.info(f'Deleting pod has been done')
    await asyncio.sleep(5.0)

    stop_event.set()
    responses, sent_ids = await send_task
    logger.info(f'Sending task has finished')
    logger.info(f'Sending task has finished: {len(sent_ids)} vs {len(responses)}')
    assert len(sent_ids) == len(responses)
    doc_ids = set()
    pod_ids = set()
    logger.info(f'Collecting doc and pod ids from responses...')
    assert len(sent_ids) == len(responses)
    for response in responses:
        doc = response.docs[0]
        doc_id, pod_id = doc.id, doc.tags['replica_uid']
        doc_ids.add(doc_id)
        pod_ids.add(pod_id)
    assert len(sent_ids) == len(doc_ids)
    logger.info(f'pod_ids {pod_ids}')
    assert len(pod_ids) >= 2  # 2 original + 2 restarted + 1 scaled up + 1 deleted

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
    await asyncio.sleep(5.0)
    # check that no message was lost
    stop_event.set()
    responses, sent_ids = await send_task
    assert len(sent_ids) == len(responses)
