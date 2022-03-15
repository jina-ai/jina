import asyncio
import json
import time

import pytest

from jina import Client, Document, Executor, requests
from jina.enums import PodRoleType, PollingType
from jina.orchestrate.pods import Pod
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.resources.health_check.gateway import (
    check_health_http,
    check_health_websocket,
)
from jina.resources.health_check.pod import check_health_pod
from jina.serve.networking import GrpcConnectionPool
from jina.types.request.control import ControlRequest


@pytest.mark.asyncio
# test gateway, head and worker pod by creating them manually in the most simple configuration
async def test_pods_trivial_topology(port_generator):
    worker_port = port_generator()
    head_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single worker pod
    worker_pod = _create_worker_pod(worker_port)

    # create a single head pod
    head_pod = _create_head_pod(head_port)

    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port)

    with gateway_pod, head_pod, worker_pod:
        # this would be done by the Pod, its adding the worker to the head
        head_pod.wait_start_success()
        worker_pod.wait_start_success()
        activate_msg = ControlRequest(command='ACTIVATE')
        activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
        assert GrpcConnectionPool.send_request_sync(
            activate_msg, f'127.0.0.1:{head_port}'
        )

        # send requests to the gateway
        gateway_pod.wait_start_success()
        c = Client(return_responses=True, host='localhost', port=port, asyncio=True)
        responses = c.post('/', inputs=async_inputs, request_size=1)

        response_list = []
        async for response in responses:
            response_list.append(response)

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'protocol, health_check',
    [
        ('grpc', check_health_pod),
        ('http', check_health_http),
        ('websocket', check_health_websocket),
    ],
)
# test pods health check
async def test_pods_health_check(port_generator, protocol, health_check):
    worker_port = port_generator()
    head_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single worker pod
    worker_pod = _create_worker_pod(worker_port)

    # create a single head pod
    head_pod = _create_head_pod(head_port)

    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port, protocol)

    with gateway_pod, head_pod, worker_pod:
        # this would be done by the Pod, its adding the worker to the head
        head_pod.wait_start_success()
        worker_pod.wait_start_success()
        activate_msg = ControlRequest(command='ACTIVATE')
        activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
        assert GrpcConnectionPool.send_request_sync(
            activate_msg, f'127.0.0.1:{head_port}'
        )

        # send requests to the gateway
        gateway_pod.wait_start_success()

        for _port in (head_port, worker_port):
            check_health_pod(f'0.0.0.0:{_port}')

        health_check(f'0.0.0.0:{port}')


@pytest.fixture
def complete_graph_dict():
    return {
        'start-gateway': ['deployment0', 'deployment4', 'deployment6'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': ['end-gateway'],
        'deployment2': ['deployment3'],
        'deployment4': ['deployment5'],
        'merger': ['deployment_last'],
        'deployment5': ['merger'],
        'deployment3': ['merger'],
        'deployment6': [],  # hanging_deployment
        'deployment_last': ['end-gateway'],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize('uses_before', [True, False])
@pytest.mark.parametrize('uses_after', [True, False])
# test gateway, head and worker pod by creating them manually in a more Flow like topology with branching/merging
async def test_pods_flow_topology(
    complete_graph_dict, uses_before, uses_after, port_generator
):
    deployments = [
        deployment_name
        for deployment_name in complete_graph_dict.keys()
        if 'gateway' not in deployment_name
    ]
    pods = []
    pod_addresses = '{'
    ports = []
    for deployment in deployments:
        if uses_before:
            uses_before_port, uses_before_pod = await _start_create_pod(
                deployment, port_generator, type='uses_before'
            )
            pods.append(uses_before_pod)
        if uses_after:
            uses_after_port, uses_after_pod = await _start_create_pod(
                deployment, port_generator, type='uses_after'
            )
            pods.append(uses_after_pod)

        # create head
        head_port = port_generator()
        pod_addresses += f'"{deployment}": ["0.0.0.0:{head_port}"],'
        head_pod = _create_head_pod(
            head_port,
            f'{deployment}/head',
            'ANY',
            f'127.0.0.1:{uses_before_port}' if uses_before else None,
            f'127.0.0.1:{uses_after_port}' if uses_after else None,
        )

        pods.append(head_pod)
        head_pod.start()

        # create worker
        worker_port, worker_pod = await _start_create_pod(deployment, port_generator)
        ports.append((head_port, worker_port))
        pods.append(worker_pod)
        await asyncio.sleep(0.1)

    for pod in pods:
        pod.wait_start_success()

    for head_port, worker_port in ports:
        await _activate_worker(head_port, worker_port)

    # remove last comma
    pod_addresses = pod_addresses[:-1]
    pod_addresses += '}'
    port = port_generator()

    # create a single gateway pod

    gateway_pod = _create_gateway_pod(
        json.dumps(complete_graph_dict), pod_addresses, port
    )
    gateway_pod.start()
    gateway_pod.wait_start_success()

    await asyncio.sleep(0.1)

    # send requests to the gateway
    c = Client(return_responses=True, host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up pod
    gateway_pod.close()
    for pod in pods:
        pod.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('polling', ['ALL', 'ANY'])
# test simple topology with shards
async def test_pods_shards(polling, port_generator):
    head_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pod
    head_pod = _create_head_pod(head_port, 'head', polling)
    head_pod.start()

    # create the shards
    shard_pods = []
    for i in range(10):
        # create worker
        worker_port = port_generator()
        # create a single worker pod
        worker_pod = _create_worker_pod(worker_port, f'pod0/shard/{i}')
        shard_pods.append(worker_pod)
        worker_pod.start()

        await asyncio.sleep(0.1)

    head_pod.wait_start_success()
    for i, pod in enumerate(shard_pods):
        # this would be done by the Pod, its adding the worker to the head
        pod.wait_start_success()
        activate_msg = ControlRequest(command='ACTIVATE')
        activate_msg.add_related_entity(
            'worker', '127.0.0.1', pod.args.port, shard_id=i
        )
        GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')

    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port)
    gateway_pod.start()

    await asyncio.sleep(1.0)

    gateway_pod.wait_start_success()
    c = Client(return_responses=True, host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up pods
    gateway_pod.close()
    head_pod.close()
    for shard_pod in shard_pods:
        shard_pod.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1 if polling == 'ANY' else len(shard_pods)


@pytest.mark.asyncio
# test simple topology with replicas
async def test_pods_replicas(port_generator):
    head_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pod
    head_pod = _create_head_pod(head_port, 'head')
    head_pod.start()

    # create the shards
    replica_pods = []
    for i in range(10):
        # create worker
        worker_port = port_generator()
        # create a single worker pod
        worker_pod = _create_worker_pod(worker_port, f'pod0/{i}')
        replica_pods.append(worker_pod)
        worker_pod.start()

        await asyncio.sleep(0.1)

    # this would be done by the Pod, its adding the worker to the head
    head_pod.wait_start_success()
    for worker_pod in replica_pods:
        worker_pod.wait_start_success()
        activate_msg = ControlRequest(command='ACTIVATE')
        activate_msg.add_related_entity('worker', '127.0.0.1', worker_pod.args.port)
        GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')

    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port)
    gateway_pod.start()

    await asyncio.sleep(1.0)

    gateway_pod.wait_start_success()
    c = Client(return_responses=True, host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up pods
    gateway_pod.close()
    head_pod.close()
    for pod in replica_pods:
        pod.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
async def test_pods_with_executor(port_generator):
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pods = []

    uses_before_port, uses_before_pod = await _start_create_pod(
        'pod0', port_generator, type='uses_before', executor='NameChangeExecutor'
    )
    pods.append(uses_before_pod)

    uses_after_port, uses_after_pod = await _start_create_pod(
        'pod0', port_generator, type='uses_after', executor='NameChangeExecutor'
    )
    pods.append(uses_after_pod)

    # create head
    head_port = port_generator()
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'
    head_pod = _create_head_pod(
        head_port,
        f'pod0/head',
        'ALL',
        f'127.0.0.1:{uses_before_port}',
        f'127.0.0.1:{uses_after_port}',
    )

    pods.append(head_pod)
    head_pod.start()

    # create some shards
    for i in range(10):
        # create worker
        worker_port, worker_pod = await _start_create_pod(
            'pod0', port_generator, type=f'shards/{i}', executor='NameChangeExecutor'
        )
        pods.append(worker_pod)
        await asyncio.sleep(0.1)
        await _activate_worker(head_port, worker_port, shard_id=i)

    for pod in pods:
        pod.wait_start_success()

    # create a single gateway pod
    port = port_generator()
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port)

    gateway_pod.start()
    gateway_pod.wait_start_success()
    pods.append(gateway_pod)

    await asyncio.sleep(1.0)

    c = Client(return_responses=True, host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1)
    response_list = []
    async for response in responses:
        response_list.append(response.docs)

    # clean up pods
    for pod in pods:
        pod.close()

    assert len(response_list) == 20
    assert (
        len(response_list[0]) == (1 + 1 + 1) * 10 + 1
    )  # 1 starting doc + 1 uses_before + every exec adds 1 * 10 shards + 1 doc uses_after

    doc_texts = [doc.text for doc in response_list[0]]
    assert doc_texts.count('client0-Request') == 10
    assert doc_texts.count('pod0/uses_before') == 10
    assert doc_texts.count('pod0/uses_after') == 1
    for i in range(10):
        assert doc_texts.count(f'pod0/shards/{i}') == 1


@pytest.mark.asyncio
async def test_pods_gateway_worker_direct_connection(port_generator):
    worker_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    worker_pod = _create_worker_pod(worker_port, f'pod0')

    worker_pod.start()

    await asyncio.sleep(0.1)
    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port)

    gateway_pod.start()

    await asyncio.sleep(1.0)

    worker_pod.wait_start_success()
    gateway_pod.wait_start_success()
    c = Client(return_responses=True, host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up pods
    gateway_pod.close()
    worker_pod.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
async def test_pods_with_replicas_advance_faster(port_generator):
    head_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pod
    head_pod = _create_head_pod(head_port, 'head')
    head_pod.start()

    # create a single gateway pod
    gateway_pod = _create_gateway_pod(graph_description, pod_addresses, port)
    gateway_pod.start()

    # create the shards
    pods = []
    for i in range(10):
        # create worker
        worker_port = port_generator()
        # create a single worker pod
        worker_pod = _create_worker_pod(worker_port, f'pod0/{i}', 'FastSlowExecutor')
        pods.append(worker_pod)
        worker_pod.start()

        await asyncio.sleep(0.1)

    head_pod.wait_start_success()
    gateway_pod.wait_start_success()
    for pod in pods:
        # this would be done by the Pod, its adding the worker to the head
        pod.wait_start_success()
        activate_msg = ControlRequest(command='ACTIVATE')
        activate_msg.add_related_entity('worker', '127.0.0.1', pod.args.port)
        GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')

    c = Client(return_responses=True, host='localhost', port=port, asyncio=True)
    input_docs = [Document(text='slow'), Document(text='fast')]
    responses = c.post('/', inputs=input_docs, request_size=1)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up pods
    gateway_pod.close()
    head_pod.close()
    for pod in pods:
        pod.close()

    assert len(response_list) == 2
    for response in response_list:
        assert len(response.docs) == 1

    assert response_list[0].docs[0].text == 'fast'
    assert response_list[1].docs[0].text == 'slow'


class NameChangeExecutor(Executor):
    def __init__(self, runtime_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = runtime_args['name']

    @requests
    def foo(self, docs, **kwargs):
        print(f'{self.name} doc count {len(docs)}')
        docs.append(Document(text=self.name))
        return docs


class FastSlowExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            if doc.text == 'slow':
                time.sleep(1.0)


async def _activate_worker(head_port, worker_port, shard_id=None):
    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity(
        'worker', '127.0.0.1', worker_port, shard_id=shard_id
    )
    GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')


async def _start_create_pod(pod, port_generator, type='worker', executor=None):
    port = port_generator()
    pod = _create_worker_pod(port, f'{pod}/{type}', executor)

    pod.start()
    return port, pod


def _create_worker_pod(port, name='', executor=None):
    args = set_pod_parser().parse_args([])
    args.port = port
    args.name = name
    args.no_block_on_start = True
    if executor:
        args.uses = executor
    return Pod(args)


def _create_head_pod(port, name='', polling='ANY', uses_before=None, uses_after=None):
    args = set_pod_parser().parse_args([])
    args.port = port
    args.name = name
    args.pod_cls = 'HeadRuntime'
    args.pod_role = PodRoleType.HEAD
    args.no_block_on_start = True
    args.polling = PollingType.ANY if polling == 'ANY' else PollingType.ALL
    if uses_before:
        args.uses_before_address = uses_before
    if uses_after:
        args.uses_after_address = uses_after

    return Pod(args)


def _create_gateway_pod(graph_description, pod_addresses, port, protocol):
    return Pod(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port',
                str(port),
                '--noblock-on-start',
                '--protocol',
                protocol,
            ]
        )
    )


async def async_inputs():
    for _ in range(20):
        yield Document(text='client0-Request')
