import asyncio
import multiprocessing
import os
import time

import pytest
from pytest_kind import cluster

from jina import Document, Flow

cluster.KIND_VERSION = 'v0.11.1'

cur_dir = os.path.dirname(__file__)


async def create_all_flow_deployments_and_wait_ready(
    flow_dump_path, namespace, api_client, app_client, core_client
):
    from kubernetes import utils

    namespace_object = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {'name': f'{namespace}'},
    }
    try:
        utils.create_from_dict(api_client, namespace_object)
    except:
        pass
    deployment_set = set(os.listdir(flow_dump_path))
    assert deployment_set == {'gateway', 'slow_process_executor'}
    for deployment_name in deployment_set:
        file_set = set(os.listdir(os.path.join(flow_dump_path, deployment_name)))
        if deployment_name == 'gateway':
            assert file_set == {'gateway.yml'}
        else:
            assert file_set == {
                'slow-process-executor.yml',
            }
        for file in file_set:
            try:
                utils.create_from_yaml(
                    api_client,
                    yaml_file=os.path.join(flow_dump_path, deployment_name, file),
                    namespace=namespace,
                )
            except Exception:
                # some objects are not successfully created since they exist from previous files
                pass

    # wait for all the pods to be up
    while True:
        namespaced_pods = core_client.list_namespaced_pod(namespace)
        if namespaced_pods.items is not None and len(namespaced_pods.items) == 4:
            break
        await asyncio.sleep(1.0)

    # wait for all the pods to be up
    resp = app_client.list_namespaced_deployment(namespace=namespace)
    deployment_names = set([item.metadata.name for item in resp.items])
    assert deployment_names == {
        'gateway',
        'slow-process-executor',
    }
    expected_replicas = {
        'gateway': 1,
        'slow-process-executor': 3,
    }
    while len(deployment_names) > 0:
        deployments_ready = []
        for deployment_name in deployment_names:
            api_response = app_client.read_namespaced_deployment(
                name=deployment_name, namespace=namespace
            )
            expected_num_replicas = expected_replicas[deployment_name]
            if (
                api_response.status.ready_replicas is not None
                and api_response.status.ready_replicas == expected_num_replicas
            ):
                deployments_ready.append(deployment_name)

        for deployment_name in deployments_ready:
            deployment_names.remove(deployment_name)
        await asyncio.sleep(1.0)


def send_requests(
    client_kwargs,
    stop_event: multiprocessing.Event,
    scale_event: multiprocessing.Event,
    received_responses: multiprocessing.Queue,
    response_arrival_times: multiprocessing.Queue,
    logger,
):
    from jina.clients import Client

    client = Client(**client_kwargs)
    client.show_progress = True

    class ResponseValidator:
        def __init__(
            self,
            received_resposes: multiprocessing.Queue,
            response_arrival_times: multiprocessing.Queue,
        ):
            self.prev_time = None
            self.received_resposes = received_resposes
            self.response_arrival_times = response_arrival_times

        def process_response(self, req):
            logger.debug(f'Received response {req.data.docs[0].text}')
            self.received_resposes.put(req.data.docs[0].text)
            if self.prev_time is not None:
                self.response_arrival_times.put(time.time() - self.prev_time)
            self.prev_time = time.time()

    validator = ResponseValidator(received_responses, response_arrival_times)

    async def async_inputs():
        for i in range(50):
            yield Document(text=f'{i}')
            if stop_event.is_set():
                logger.debug(f'stop sending new requests after {i} requests')
            else:
                await asyncio.sleep(1.0 if scale_event.is_set() else 0.05)

    client.post(
        '/',
        inputs=async_inputs,
        request_size=1,
        on_done=validator.process_response,
        return_responses=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images', [['slow-process-executor', 'jinaai/jina']], indirect=True
)
async def test_no_message_lost_during_scaling(logger, docker_images, tmpdir):
    flow = Flow(name='test-flow-slow-process-executor',).add(
        name='slow_process_executor',
        uses=f'docker://{docker_images[0]}',
        replicas=3,
    )

    dump_path = os.path.join(str(tmpdir), 'test_flow_k8s')
    namespace = 'test-flow-slow-process-executor-ns'
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
    )

    # start port forwarding
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
        # send requests and validate
        time.sleep(0.1)
        client_kwargs = dict(
            host='localhost',
            port=flow.port,
        )
        client_kwargs.update(flow._common_kwargs)

        stop_event = multiprocessing.Event()
        scale_event = multiprocessing.Event()
        received_responses = multiprocessing.Queue()
        response_arrival_times = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=send_requests,
            kwargs={
                'client_kwargs': client_kwargs,
                'stop_event': stop_event,
                'scale_event': scale_event,
                'received_responses': received_responses,
                'response_arrival_times': response_arrival_times,
                'logger': logger,
            },
            daemon=True,
        )
        process.start()
        time.sleep(1.0)
        logger.debug('Scale down executor to 1 replica')
        app_client.patch_namespaced_deployment_scale(
            'slow-process-executor',
            namespace=namespace,
            body={'spec': {'replicas': 1}},
        )
        scale_event.set()
        # wait for replicas to be dead
        while True:
            pods = core_client.list_namespaced_pod(
                namespace=namespace,
                label_selector=f'app=slow-process-executor',
            )
            if len(pods.items) == 1:
                # still continue for a bit to hit the new replica only
                logger.debug('Scale down complete')
                time.sleep(1.0)
                stop_event.set()
                break
            await asyncio.sleep(1.0)
        await asyncio.sleep(10.0)
        # kill the process as the client can hang due to lost responsed
        if process.is_alive():
            process.kill()
        process.join()

        responses_list = []
        while not received_responses.empty():
            responses_list.append(int(received_responses.get()))

        logger.debug(f'Got the following responses {sorted(responses_list)}')
        assert sorted(responses_list) == list(
            range(min(responses_list), max(responses_list) + 1)
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images', [['slow-process-executor', 'jinaai/jina']], indirect=True
)
async def test_no_message_lost_during_kill(logger, docker_images, tmpdir):
    flow = Flow(name='test-flow-slow-process-executor',).add(
        name='slow_process_executor',
        uses=f'docker://{docker_images[0]}',
        replicas=3,
    )
    dump_path = os.path.join(str(tmpdir), 'test_flow_k8s')
    namespace = 'test-flow-slow-process-executor-ns-2'
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
    )

    # start port forwarding
    logger.debug(f' Start port forwarding')
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
        # send requests and validate
        time.sleep(0.1)
        client_kwargs = dict(
            host='localhost',
            port=flow.port,
        )
        client_kwargs.update(flow._common_kwargs)

        stop_event = multiprocessing.Event()
        scale_event = multiprocessing.Event()
        received_responses = multiprocessing.Queue()
        response_arrival_times = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=send_requests,
            kwargs={
                'client_kwargs': client_kwargs,
                'stop_event': stop_event,
                'scale_event': scale_event,
                'received_responses': received_responses,
                'response_arrival_times': response_arrival_times,
                'logger': logger,
            },
            daemon=True,
        )
        process.start()
        time.sleep(1.0)
        logger.debug('Kill 2 replicas')

        pods = core_client.list_namespaced_pod(
            namespace=namespace,
            label_selector=f'app=slow-process-executor',
        )

        names = [item.metadata.name for item in pods.items]
        core_client.delete_namespaced_pod(names[0], namespace=namespace)
        core_client.delete_namespaced_pod(names[1], namespace=namespace)

        scale_event.set()
        # wait for replicas to be dead
        while True:
            pods = core_client.list_namespaced_pod(
                namespace=namespace,
                label_selector=f'app=slow-process-executor',
            )
            current_pod_names = [item.metadata.name for item in pods.items]
            if names[0] not in current_pod_names and names[1] not in current_pod_names:
                logger.debug('Killing pods complete')
                time.sleep(1.0)
                stop_event.set()
                break
            else:
                logger.debug(
                    f'not dead yet {current_pod_names} waiting for {names[0]} and {names[1]}'
                )
            time.sleep(1.0)

        process.join()

        responses_list = []
        while not received_responses.empty():
            responses_list.append(int(received_responses.get()))

        logger.debug(f'Got the following responses {sorted(responses_list)}')
        assert sorted(responses_list) == list(
            range(min(responses_list), max(responses_list) + 1)
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images', [['slow-process-executor', 'jinaai/jina']], indirect=True
)
async def test_linear_processing_time_scaling(docker_images, logger, tmpdir):
    flow = Flow(name='test-flow-slow-process-executor',).add(
        name='slow_process_executor',
        uses=f'docker://{docker_images[0]}',
        replicas=3,
    )
    dump_path = os.path.join(str(tmpdir), 'test_flow_k8s')
    namespace = 'test-flow-slow-process-executor-ns-3'
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
    )

    # start port forwarding
    logger.debug(f' Start port forwarding')
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
        time.sleep(0.1)
        client_kwargs = dict(
            host='localhost',
            port=flow.port,
        )
        client_kwargs.update(flow._common_kwargs)

        stop_event = multiprocessing.Event()
        scale_event = multiprocessing.Event()
        received_responses = multiprocessing.Queue()
        response_arrival_times = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=send_requests,
            kwargs={
                'client_kwargs': client_kwargs,
                'stop_event': stop_event,
                'scale_event': scale_event,
                'received_responses': received_responses,
                'response_arrival_times': response_arrival_times,
                'logger': logger,
            },
        )

        process.start()
        process.join()
        import numpy as np

        response_times = []
        while not response_arrival_times.empty():
            response_times.append(response_arrival_times.get())
        mean_response_time = np.mean(response_times)
        logger.debug(
            f'Mean time between responses is {mean_response_time}, expected is 1/3 second'
        )
        assert mean_response_time < 0.4

        responses_list = []
        while not received_responses.empty():
            responses_list.append(int(received_responses.get()))

        logger.debug(f'Got the following responses {sorted(responses_list)}')
        assert sorted(responses_list) == list(
            range(min(responses_list), max(responses_list) + 1)
        )
