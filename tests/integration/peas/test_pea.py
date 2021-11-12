import asyncio
import json
import multiprocessing
import time

import pytest

from jina import Document, Executor, Client, requests
from jina.enums import PollingType, PeaRoleType
from jina.helper import random_port
from jina.parsers import set_gateway_parser, set_pea_parser
from jina.peapods.networking import GrpcConnectionPool
from jina.peapods.peas import BasePea
from jina.peapods.runtimes.head import HeadRuntime
from jina.peapods.runtimes.worker import WorkerRuntime
from jina.types.message.common import ControlMessage


@pytest.mark.asyncio
# test gateway, head and worker pea by creating them manually in the most simple configuration
async def test_peas_trivial_topology():
    worker_port = random_port()
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single worker pea
    worker_pea = _create_worker_pea(worker_port)

    worker_pea.start()

    # create a single head pea
    head_pea = _create_head_pea(head_port)

    head_pea.start()

    # create a single gateway pea
    gateway_pea = _create_gateway_pea(graph_description, pod_addresses, port_expose)

    gateway_pea.start()

    await asyncio.sleep(1.0)

    assert HeadRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{head_port}',
        shutdown_event=multiprocessing.Event(),
    )

    assert WorkerRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        shutdown_event=multiprocessing.Event(),
    )

    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlMessage(command='ACTIVATE')
    activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
    assert GrpcConnectionPool.send_message_sync(activate_msg, f'127.0.0.1:{head_port}')

    # send requests to the gateway
    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up peas
    gateway_pea.close()
    head_pea.close()
    worker_pea.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.fixture
def complete_graph_dict():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['end-gateway'],
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'merger': ['pod_last'],
        'pod5': ['merger'],
        'pod3': ['merger'],
        'pod6': [],  # hanging_pod
        'pod_last': ['end-gateway'],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize('uses_before', [True, False])
@pytest.mark.parametrize('uses_after', [True, False])
# test gateway, head and worker pea by creating them manually in a more Flow like topology with branching/merging
async def test_peas_flow_topology(complete_graph_dict, uses_before, uses_after):
    pods = [
        pod_name for pod_name in complete_graph_dict.keys() if 'gateway' not in pod_name
    ]
    peas = []
    pod_addresses = '{'
    for pod in pods:
        if uses_before:
            uses_before_port, uses_before_pea = await _start_create_pea(
                pod, type='uses_before'
            )
            peas.append(uses_before_pea)
        if uses_after:
            uses_after_port, uses_after_pea = await _start_create_pea(
                pod, type='uses_after'
            )
            peas.append(uses_after_pea)

        # create head
        head_port = random_port()
        pod_addresses += f'"{pod}": ["0.0.0.0:{head_port}"],'
        head_pea = _create_head_pea(
            head_port,
            f'{pod}/head',
            'ANY',
            f'127.0.0.1:{uses_before_port}' if uses_before else None,
            f'127.0.0.1:{uses_after_port}' if uses_after else None,
        )

        peas.append(head_pea)
        head_pea.start()

        # create worker
        worker_port, worker_pea = await _start_create_pea(pod)
        peas.append(worker_pea)
        await asyncio.sleep(0.1)

        await _activate_worker(head_port, worker_port)

    # remove last comma
    pod_addresses = pod_addresses[:-1]
    pod_addresses += '}'
    port_expose = random_port()

    # create a single gateway pea

    gateway_pea = _create_gateway_pea(
        json.dumps(complete_graph_dict), pod_addresses, port_expose
    )
    gateway_pea.start()

    await asyncio.sleep(0.1)

    # send requests to the gateway
    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up pea
    gateway_pea.close()
    for pea in peas:
        pea.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize('polling', ['ALL', 'ANY'])
# test simple topology with shards
async def test_peas_shards(polling):
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pea
    head_pea = _create_head_pea(head_port, 'head', polling)
    head_pea.start()

    # create the shards
    shard_peas = []
    for i in range(10):
        # create worker
        worker_port = random_port()
        # create a single worker pea
        worker_pea = _create_worker_pea(worker_port, f'pod0/shard/{i}')
        shard_peas.append(worker_pea)
        worker_pea.start()

        await asyncio.sleep(0.1)

        # this would be done by the Pod, its adding the worker to the head
        activate_msg = ControlMessage(command='ACTIVATE')
        activate_msg.add_related_entity('worker', '127.0.0.1', worker_port, shard_id=i)
        assert GrpcConnectionPool.send_message_sync(
            activate_msg, f'127.0.0.1:{head_port}'
        )

    # create a single gateway pea
    gateway_pea = _create_gateway_pea(graph_description, pod_addresses, port_expose)
    gateway_pea.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up peas
    gateway_pea.close()
    head_pea.close()
    for shard_pea in shard_peas:
        shard_pea.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1 if polling == 'ANY' else len(shard_peas)


@pytest.mark.asyncio
# test simple topology with replicas
async def test_peas_replicas():
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pea
    head_pea = _create_head_pea(head_port, 'head')
    head_pea.start()

    # create the shards
    replica_peas = []
    for i in range(10):
        # create worker
        worker_port = random_port()
        # create a single worker pea
        worker_pea = _create_worker_pea(worker_port, f'pod0/{i}')
        replica_peas.append(worker_pea)
        worker_pea.start()

        await asyncio.sleep(0.1)

        # this would be done by the Pod, its adding the worker to the head
        activate_msg = ControlMessage(command='ACTIVATE')
        activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
        assert GrpcConnectionPool.send_message_sync(
            activate_msg, f'127.0.0.1:{head_port}'
        )

    # create a single gateway pea
    gateway_pea = _create_gateway_pea(graph_description, pod_addresses, port_expose)
    gateway_pea.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up peas
    gateway_pea.close()
    head_pea.close()
    for pea in replica_peas:
        pea.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
async def test_peas_with_executor():
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    peas = []

    uses_before_port, uses_before_pea = await _start_create_pea(
        'pod0', type='uses_before', executor='NameChangeExecutor'
    )
    peas.append(uses_before_pea)

    uses_after_port, uses_after_pea = await _start_create_pea(
        'pod0', type='uses_after', executor='NameChangeExecutor'
    )
    peas.append(uses_after_pea)

    # create head
    head_port = random_port()
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'
    head_pea = _create_head_pea(
        head_port,
        f'pod0/head',
        'ALL',
        f'127.0.0.1:{uses_before_port}',
        f'127.0.0.1:{uses_after_port}',
    )

    peas.append(head_pea)
    head_pea.start()

    # create some shards
    for i in range(10):
        # create worker
        worker_port, worker_pea = await _start_create_pea(
            'pod0', type=f'shards/{i}', executor='NameChangeExecutor'
        )
        peas.append(worker_pea)
        await asyncio.sleep(0.1)

        await _activate_worker(head_port, worker_port, shard_id=i)

    # create a single gateway pea
    port_expose = random_port()
    gateway_pea = _create_gateway_pea(graph_description, pod_addresses, port_expose)

    gateway_pea.start()
    peas.append(gateway_pea)

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response.docs)

    # clean up peas
    for pea in peas:
        pea.close()

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
async def test_peas_gateway_worker_direct_connection():
    worker_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    worker_pea = _create_worker_pea(worker_port, f'pod0')

    worker_pea.start()

    await asyncio.sleep(0.1)
    # create a single gateway pea
    gateway_pea = _create_gateway_pea(graph_description, pod_addresses, port_expose)

    gateway_pea.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up peas
    gateway_pea.close()
    worker_pea.close()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
async def test_peas_with_replicas_advance_faster():
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pea
    head_pea = _create_head_pea(head_port, 'head')
    head_pea.start()

    # create the shards
    peas = []
    for i in range(10):
        # create worker
        worker_port = random_port()
        # create a single worker pea
        worker_pea = _create_worker_pea(worker_port, f'pod0/{i}', 'FastSlowExecutor')
        peas.append(worker_pea)
        worker_pea.start()

        await asyncio.sleep(0.1)

        # this would be done by the Pod, its adding the worker to the head
        activate_msg = ControlMessage(command='ACTIVATE')
        activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
        assert GrpcConnectionPool.send_message_sync(
            activate_msg, f'127.0.0.1:{head_port}'
        )

    # create a single gateway pea
    gateway_pea = _create_gateway_pea(graph_description, pod_addresses, port_expose)
    gateway_pea.start()

    await asyncio.sleep(1.0)

    c = Client(host='localhost', port=port_expose, asyncio=True)
    input_docs = [Document(text='slow'), Document(text='fast')]
    responses = c.post('/', inputs=input_docs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up peas
    gateway_pea.close()
    head_pea.close()
    for pea in peas:
        pea.close()

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
    activate_msg = ControlMessage(command='ACTIVATE')
    activate_msg.add_related_entity(
        'worker', '127.0.0.1', worker_port, shard_id=shard_id
    )
    assert GrpcConnectionPool.send_message_sync(activate_msg, f'127.0.0.1:{head_port}')


async def _start_create_pea(pod, type='worker', executor=None):
    port = random_port()
    pea = _create_worker_pea(port, f'{pod}/{type}', executor)

    pea.start()
    return port, pea


def _create_worker_pea(port, name='', executor=None):
    args = set_pea_parser().parse_args([])
    args.port_in = port
    args.name = name
    if executor:
        args.uses = executor
    return BasePea(args)


def _create_head_pea(port, name='', polling='ANY', uses_before=None, uses_after=None):
    args = set_pea_parser().parse_args([])
    args.port_in = port
    args.name = name
    args.pea_cls = 'HeadRuntime'
    args.pea_role = PeaRoleType.HEAD
    args.polling = PollingType.ANY if polling == 'ANY' else PollingType.ALL
    if uses_before:
        args.uses_before_address = uses_before
    if uses_after:
        args.uses_after_address = uses_after

    return BasePea(args)


def _create_gateway_pea(graph_description, pod_addresses, port_expose):
    return BasePea(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--pods-addresses',
                pod_addresses,
                '--port-expose',
                str(port_expose),
            ]
        )
    )


async def async_inputs():
    for _ in range(20):
        yield Document(text='client0-Request')
