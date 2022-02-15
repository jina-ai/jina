import os
import asyncio
import multiprocessing
import time

import pytest

from jina import Document, Client
from jina.enums import PollingType, PodRoleType
from jina.helper import random_port
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.serve.networking import GrpcConnectionPool
from jina.orchestrate.pods.container import ContainerPod
from jina.orchestrate.pods import Pod
from jina.serve.runtimes.head import HeadRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from jina.types.request.control import ControlRequest

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
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single worker pod
    worker_pod = _create_worker_pod(worker_port)

    # create a single head pod
    head_pod = _create_head_pod(head_port)

    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port_expose)

    with gateway_pod, worker_pod, head_pod:
        await asyncio.sleep(1.0)

        assert HeadRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=head_pod.runtime_ctrl_address,
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        assert WorkerRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=worker_pod.runtime_ctrl_address,
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        # this would be done by the Pod, its adding the worker to the head
        activate_msg = ControlRequest(command='ACTIVATE')
        worker_host, worker_port = worker_pod.runtime_ctrl_address.split(':')
        activate_msg.add_related_entity('worker', worker_host, int(worker_port))
        assert GrpcConnectionPool.send_request_sync(
            activate_msg, head_pod.runtime_ctrl_address
        )

        # send requests to the gateway
        c = Client(
            return_responses=True, host='localhost', port=port_expose, asyncio=True
        )
        responses = c.post(
            '/', inputs=async_inputs, request_size=1, return_results=True
        )
        response_list = []
        async for response in responses:
            response_list.append(response)

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


def _create_worker_pod(port):
    args = set_pod_parser().parse_args([])
    args.port_in = port
    args.name = 'worker'
    args.uses = 'docker://worker-runtime'
    return ContainerPod(args)


def _create_head_pod(port):
    args = set_pod_parser().parse_args([])
    args.port_in = port
    args.name = 'head'
    args.pod_role = PodRoleType.HEAD
    args.polling = PollingType.ANY
    args.uses = 'docker://head-runtime'
    return ContainerPod(args)


def _create_gateway_pod(graph_description, pod_addresses, port_expose):
    return Pod(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port-expose',
                str(port_expose),
            ]
        )
    )


async def async_inputs():
    for _ in range(20):
        yield Document(text='client0-Request')
