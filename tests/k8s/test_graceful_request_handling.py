import asyncio
import multiprocessing
import os
import signal
import time
from multiprocessing import Process

import docker
import pytest

from jina import Flow, Document
from jina.peapods.pods.k8slib import kubernetes_tools
from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


def send_requests(
    client_kwargs,
    stop_event: multiprocessing.Event,
    scale_event: multiprocessing.Event,
    received_resposes: multiprocessing.Queue,
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

    validator = ResponseValidator(received_resposes, response_arrival_times)

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
    )


@pytest.mark.asyncio
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='this actually does not work, there are messages lost when shutting down k8s pods',
)
async def test_no_message_lost_during_scaling(
    slow_process_executor_image,
    logger,
    k8s_cluster,
    load_images_in_kind,
    set_test_pip_version,
):
    flow = Flow(
        name='test-flow-slow-process-executor',
        infrastructure='K8S',
        timeout_ready=120000,
        k8s_namespace='test-flow-slow-process-executor-ns',
    ).add(
        name='slow_process_executor',
        uses=slow_process_executor_image,
        timeout_ready=360000,
        replicas=3,
        grpc_data_requests=True,
    )

    with flow:
        with kubernetes_tools.get_port_forward_contextmanager(
            'test-flow-slow-process-executor', flow.port_expose
        ):
            # sleep as the port forward setup can take some time
            time.sleep(0.1)
            client_kwargs = dict(
                host='localhost',
                port=flow.port_expose,
            )
            client_kwargs.update(flow._common_kwargs)

            stop_event = multiprocessing.Event()
            scale_event = multiprocessing.Event()
            received_resposes = multiprocessing.Queue()
            process = Process(
                target=send_requests,
                kwargs={
                    'client_kwargs': client_kwargs,
                    'stop_event': stop_event,
                    'scale_event': scale_event,
                    'received_resposes': received_resposes,
                    'logger': logger,
                },
                daemon=True,
            )
            process.start()

            time.sleep(1.0)

            # scale slow init executor up
            k8s_clients = K8sClients()
            logger.debug('Scale down executor to 1 replica')
            k8s_clients.apps_v1.patch_namespaced_deployment_scale(
                'slow-process-executor',
                namespace='test-flow-slow-process-executor',
                body={"spec": {"replicas": 1}},
            )
            scale_event.set()

            # wait for replicas to be dead
            while True:
                pods = k8s_clients.core_v1.list_namespaced_pod(
                    namespace='test-flow-slow-process-executor',
                    label_selector=f'app=slow-process-executor',
                )
                if len(pods.items) == 1:
                    # still continue for a bit to hit the new replica only
                    logger.debug('Scale down complete')
                    time.sleep(1.0)
                    stop_event.set()
                    break
                await asyncio.sleep(1.0)

            # allow some time for responses to complete
            await asyncio.sleep(10.0)
            # kill the process as the client can hang due to lost responsed
            if process.is_alive():
                process.kill()
            process.join()

            responses_list = []
            while received_resposes.qsize():
                responses_list.append(int(received_resposes.get()))

            logger.debug(f'Got the following responses {sorted(responses_list)}')
            assert sorted(responses_list) == list(
                range(min(responses_list), max(responses_list) + 1)
            )


@pytest.mark.asyncio
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='this actually does not work, there are messages lost when shutting down k8s pods',
)
async def test_no_message_lost_during_kill(
    slow_process_executor_image,
    logger,
    k8s_cluster,
    load_images_in_kind,
    set_test_pip_version,
):
    flow = Flow(
        name='test-flow-slow-process-executor',
        infrastructure='K8S',
        timeout_ready=120000,
        k8s_namespace='test-flow-slow-process-executor-ns',
    ).add(
        name='slow_process_executor',
        uses=slow_process_executor_image,
        timeout_ready=360000,
        replicas=3,
        grpc_data_requests=True,
    )

    with flow:
        with kubernetes_tools.get_port_forward_contextmanager(
            'test-flow-slow-process-executor', flow.port_expose
        ):
            client_kwargs = dict(
                host='localhost',
                port=flow.port_expose,
            )
            client_kwargs.update(flow._common_kwargs)

            stop_event = multiprocessing.Event()
            scale_event = multiprocessing.Event()
            received_resposes = multiprocessing.Queue()
            process = Process(
                target=send_requests,
                kwargs={
                    'client_kwargs': client_kwargs,
                    'stop_event': stop_event,
                    'scale_event': scale_event,
                    'received_resposes': received_resposes,
                    'logger': logger,
                },
                daemon=True,
            )
            process.start()

            time.sleep(1.0)

            # scale slow init executor up
            k8s_clients = K8sClients()
            logger.debug('Kill 2 replicas')

            pods = k8s_clients.core_v1.list_namespaced_pod(
                namespace='test-flow-slow-process-executor',
                label_selector=f'app=slow-process-executor',
            )

            names = [item.metadata.name for item in pods.items]
            k8s_clients.core_v1.delete_namespaced_pod(
                names[0], namespace='test-flow-slow-process-executor'
            )
            k8s_clients.core_v1.delete_namespaced_pod(
                names[1], namespace='test-flow-slow-process-executor'
            )

            scale_event.set()

            # wait for replicas to be dead
            while True:
                pods = k8s_clients.core_v1.list_namespaced_pod(
                    namespace='test-flow-slow-process-executor',
                    label_selector=f'app=slow-process-executor',
                )
                current_pod_names = [item.metadata.name for item in pods.items]
                if (
                    names[0] not in current_pod_names
                    and names[1] not in current_pod_names
                ):
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
            while received_resposes.qsize():
                responses_list.append(int(received_resposes.get()))

            logger.debug(f'Got the following responses {sorted(responses_list)}')
            assert sorted(responses_list) == list(
                range(min(responses_list), max(responses_list) + 1)
            )


def test_linear_processing_time_scaling(
    slow_process_executor_image,
    logger,
    k8s_cluster,
    load_images_in_kind,
    set_test_pip_version,
):
    flow = Flow(
        name='test-flow-slow-process-executor',
        infrastructure='K8S',
        timeout_ready=120000,
        k8s_namespace='test-flow-slow-process-executor-ns',
    ).add(
        name='slow_process_executor',
        uses=slow_process_executor_image,
        timeout_ready=360000,
        replicas=3,
        grpc_data_requests=True,
    )

    with flow:
        with kubernetes_tools.get_port_forward_contextmanager(
            'test-flow-slow-process-executor-ns', flow.port_expose
        ):
            # sleep as the port forward setup can take some time
            time.sleep(0.1)
            client_kwargs = dict(
                host='localhost',
                port=flow.port_expose,
            )
            client_kwargs.update(flow._common_kwargs)

            stop_event = multiprocessing.Event()
            scale_event = multiprocessing.Event()
            received_resposes = multiprocessing.Queue()
            response_arrival_times = multiprocessing.Queue()
            process = Process(
                target=send_requests,
                kwargs={
                    'client_kwargs': client_kwargs,
                    'stop_event': stop_event,
                    'scale_event': scale_event,
                    'received_resposes': received_resposes,
                    'response_arrival_times': response_arrival_times,
                    'logger': logger,
                },
            )

            process.start()
            process.join()

            import numpy as np

            response_times = []
            while response_arrival_times.qsize():
                response_times.append(response_arrival_times.get())
            mean_response_time = np.mean(response_times)
            logger.debug(
                f'Mean time between responses is {mean_response_time}, expected is 1/3 second'
            )
            assert mean_response_time < 0.4

            responses_list = []
            while received_resposes.qsize():
                responses_list.append(int(received_resposes.get()))

            logger.debug(f'Got the following responses {sorted(responses_list)}')
            assert sorted(responses_list) == list(
                range(min(responses_list), max(responses_list) + 1)
            )
