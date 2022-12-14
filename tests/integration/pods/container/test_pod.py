import asyncio
import json
import os
import time

import pytest

from jina import Client, Document
from jina.enums import PodRoleType, PollingType
from jina.helper import random_port
from jina.orchestrate.pods import Pod
from jina.orchestrate.pods.container import ContainerPod
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.head import HeadRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from tests.helper import _generate_pod_args

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def head_runtime_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'head-runtime/'), tag='head-runtime')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.fixture(scope='module')
def worker_runtime_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'worker-runtime/'), tag='worker-runtime'
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.asyncio
# test gateway, head and worker pod by creating them manually in the most simple configuration
async def test_pods_trivial_topology(
    head_runtime_docker_image_built, worker_runtime_docker_image_built
):
    worker_port = random_port()
    head_port = random_port()
    port = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single worker pod
    worker_pod = _create_worker_pod(worker_port)

    # this would be done by the Pod, its adding the worker to the head
    worker_host, worker_port = worker_pod.runtime_ctrl_address.split(':')
    connection_list_dict = {'0': [f'{worker_host}:{worker_port}']}

    # create a single head pod
    head_pod = _create_head_pod(head_port, connection_list_dict)

    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port)

    with gateway_pod, head_pod, worker_pod:
        await asyncio.sleep(1.0)

        assert HeadRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=head_pod.runtime_ctrl_address,
            ready_or_shutdown_event=head_pod.ready_or_shutdown.event,
        )

        assert WorkerRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=worker_pod.runtime_ctrl_address,
            ready_or_shutdown_event=worker_pod.ready_or_shutdown.event,
        )

        head_pod.ready_or_shutdown.event.wait(timeout=5.0)
        worker_pod.ready_or_shutdown.event.wait(timeout=5.0)
        gateway_pod.ready_or_shutdown.event.wait(timeout=5.0)

        # send requests to the gateway
        c = Client(host='localhost', port=port, asyncio=True)
        responses = c.post(
            '/', inputs=async_inputs, request_size=1, return_responses=True
        )
        response_list = []
        async for response in responses:
            response_list.append(response)

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


def _create_worker_pod(port):
    args = _generate_pod_args()
    args.port = port
    args.name = 'worker'
    args.uses = 'docker://worker-runtime'
    return ContainerPod(args)


def _create_head_pod(port, connection_list_dict):
    args = _generate_pod_args()
    args.port = port
    args.name = 'head'
    args.pod_role = PodRoleType.HEAD
    args.polling = PollingType.ANY
    args.uses = 'docker://head-runtime'
    args.connection_list = json.dumps(connection_list_dict)
    return ContainerPod(args)


def _create_gateway_pod(graph_description, pod_addresses, port):
    return Pod(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port',
                str(port),
            ]
        )
    )


async def async_inputs():
    for _ in range(20):
        yield Document(text='client0-Request')
