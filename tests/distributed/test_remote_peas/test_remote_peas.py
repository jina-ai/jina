import asyncio
import multiprocessing
import os
import threading

import pytest

from daemon.clients import AsyncJinaDClient, JinaDClient
from daemon.models.id import DaemonID
from jina import Client, Document, __default_host__, __docker_host__
from jina.enums import PeaRoleType, PollingType, replace_enum_to_str
from jina.helper import random_port
from jina.parsers import set_gateway_parser, set_pea_parser
from jina.peapods.networking import GrpcConnectionPool
from jina.peapods.peas.factory import PeaFactory
from jina.peapods.peas.helper import is_ready
from jina.peapods.peas.jinad import JinaDPea, JinaDProcessTarget
from jina.types.request.control import ControlRequest

HOST = '127.0.0.1'
PORT = 8000
cur_dir = os.path.dirname(os.path.abspath(__file__))
is_remote = lambda l_or_r: l_or_r == 'remote'


def is_pea_ready(args):
    return is_ready(f'{HOST}:{args.port_in}')


@pytest.fixture
def pea_args():
    return set_pea_parser().parse_args([])


@pytest.fixture
def jinad_client():
    return JinaDClient(host=HOST, port=PORT)


@pytest.fixture
def async_jinad_client():
    return AsyncJinaDClient(host=HOST, port=PORT)


@pytest.mark.asyncio
async def test_async_jinad_client(async_jinad_client, pea_args):
    workspace_id = await async_jinad_client.workspaces.create(paths=[cur_dir])
    assert DaemonID(workspace_id)

    success, pea_id = await async_jinad_client.peas.create(
        workspace_id=workspace_id, payload=replace_enum_to_str(vars(pea_args))
    )
    assert success
    assert pea_id
    assert is_pea_ready(pea_args)
    assert await async_jinad_client.peas.delete(pea_id)
    assert not is_pea_ready(pea_args)
    assert await async_jinad_client.workspaces.delete(workspace_id)


def test_sync_jinad_client(jinad_client, pea_args):
    workspace_id = jinad_client.workspaces.create(paths=[cur_dir])
    assert DaemonID(workspace_id)

    success, pea_id = jinad_client.peas.create(
        workspace_id=workspace_id, payload=replace_enum_to_str(vars(pea_args))
    )
    assert success
    assert pea_id
    assert is_pea_ready(pea_args)
    assert jinad_client.peas.delete(pea_id)
    assert not is_pea_ready(pea_args)
    assert jinad_client.workspaces.delete(workspace_id)


def test_jinad_process_target(pea_args):
    is_started_event, is_shutdown_event, is_ready_event, is_cancelled_event = [
        multiprocessing.Event()
    ] * 4

    process = multiprocessing.Process(
        target=JinaDProcessTarget(),
        kwargs={
            'args': pea_args,
            'is_started': is_started_event,
            'is_shutdown': is_shutdown_event,
            'is_ready': is_ready_event,
            'is_cancelled': is_cancelled_event,
        },
    )
    process.start()
    is_ready_event.wait()
    check_is_pea_ready = is_pea_ready(pea_args)
    process.join()
    assert check_is_pea_ready
    assert is_shutdown_event.is_set()
    assert not is_pea_ready(pea_args)


def test_jinad_pea():
    args = set_pea_parser().parse_args([])
    assert not is_pea_ready(args)

    with JinaDPea(args):
        assert is_pea_ready(args)
    assert not is_pea_ready(args)


async def _activate_worker(
    head_host, head_port, worker_host, worker_port, shard_id=None
):
    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity(
        'worker', worker_host, worker_port, shard_id=shard_id
    )
    GrpcConnectionPool.send_request_sync(activate_msg, f'{head_host}:{head_port}')


def _create_worker_pea(
    l_or_r,
    port,
    name='',
    executor=None,
    py_modules=None,
    upload_files=None,
):
    args = set_pea_parser().parse_args([])
    if is_remote(l_or_r):
        args.host = HOST
        args.port_jinad = PORT
    args.name = name if name else f'worker-{l_or_r}'
    args.port_in = port
    args.runtime_cls = 'WorkerRuntime'
    if executor:
        args.uses = executor
    if upload_files:
        args.upload_files = upload_files
    if py_modules:
        args.py_modules = [py_modules]
    return PeaFactory.build_pea(args)


def _create_head_pea(
    l_or_r, port, polling=PollingType.ANY, name='', uses_before=None, uses_after=None
):
    args = set_pea_parser().parse_args([])
    if is_remote(l_or_r):
        args.host = HOST
        args.port_jinad = PORT
    args.name = name if name else f'head-{l_or_r}'
    args.port_in = port
    args.pea_role = PeaRoleType.HEAD
    args.polling = polling
    args.runtime_cls = 'HeadRuntime'
    if uses_before:
        args.uses_before_address = uses_before
    if uses_after:
        args.uses_after_address = uses_after
    return PeaFactory.build_pea(args)


def _create_gateway_pea(l_or_r, graph_description, pods_addresses, port_expose):
    args = set_gateway_parser().parse_args([])
    if l_or_r == 'remote':
        args.host = HOST
        args.port_jinad = PORT
    args.graph_description = graph_description
    args.pods_addresses = pods_addresses
    args.port_expose = port_expose
    args.runtime_cls = 'GRPCGatewayRuntime'
    return PeaFactory.build_pea(args)


async def async_inputs():
    for i in range(20):
        yield Document(text=f'client0-Request')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'gateway, head, worker',
    [
        ('local', 'local', 'local'),
        ('local', 'local', 'remote'),
        ('local', 'remote', 'remote'),
    ],
)
async def test_pseudo_remote_peas_topologies(gateway, head, worker):
    """
    g(l)-h(l)-w(l) - works
    g(l)-h(l)-w(r) - works - head connects to worker via localhost
    g(l)-h(r)-w(r) - works - head (inside docker) connects to worker via dockerhost
    g(l)-h(r)-w(l) - doesn't work remote head need remote worker
    g(r)-... - doesn't work, as distributed parser not enabled for gateway
    After any 1 failure, segfault
    """
    worker_port = random_port()
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    if head == 'remote':
        pods_addresses = f'{{"pod0": ["{HOST}:{head_port}"]}}'
    else:
        pods_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pea
    head_pea = _create_head_pea(head, head_port)

    # create a single worker pea
    worker_pea = _create_worker_pea(worker, worker_port)

    # create a single gateway pea
    gateway_pea = _create_gateway_pea(
        gateway, graph_description, pods_addresses, port_expose
    )

    with gateway_pea, worker_pea, head_pea:
        await asyncio.sleep(1.0)
        # this would be done by the Pod, its adding the worker to the head
        activate_msg = ControlRequest(command='ACTIVATE')
        worker_host, worker_port = worker_pea.runtime_ctrl_address.split(':')
        if head == 'remote':
            worker_host = __docker_host__

        activate_msg.add_related_entity('worker', worker_host, int(worker_port))
        assert GrpcConnectionPool.send_request_sync(
            activate_msg, head_pea.runtime_ctrl_address
        )

        # send requests to the gateway
        c = Client(host='127.0.0.1', port=port_expose, asyncio=True)
        responses = c.post(
            '/', inputs=async_inputs, request_size=1, return_results=True
        )
        response_list = []
        async for response in responses:
            response_list.append(response)

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'gateway, head, worker',
    [
        ('local', 'local', 'local'),
        ('local', 'local', 'remote'),
        ('local', 'remote', 'remote'),
    ],
)
@pytest.mark.parametrize('polling', [PollingType.ANY, PollingType.ALL])
# test simple topology with shards on remote
async def test_pseudo_remote_peas_shards(gateway, head, worker, polling):
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pods_addresses = f'{{"pod0": ["{HOST}:{head_port}"]}}'

    # create a single head pea
    head_pea = _create_head_pea(head, head_port, polling)
    head_pea.start()

    # create the shards
    shard_peas = []
    for i in range(3):
        # create worker
        worker_port = random_port()
        # create a single worker pea
        worker_pea = _create_worker_pea(worker, worker_port, f'pod0/shard/{i}')
        shard_peas.append(worker_pea)
        worker_pea.start()

        await asyncio.sleep(0.1)

        if head == 'remote':
            worker_host = __docker_host__
        else:
            worker_host = HOST

        # this would be done by the Pod, its adding the worker to the head
        activate_msg = ControlRequest(command='ACTIVATE')
        activate_msg.add_related_entity('worker', worker_host, worker_port, shard_id=i)
        GrpcConnectionPool.send_request_sync(activate_msg, f'{HOST}:{head_port}')

    # create a single gateway pea
    gateway_pea = _create_gateway_pea(
        gateway, graph_description, pods_addresses, port_expose
    )
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
@pytest.mark.parametrize(
    'gateway, head, worker',
    [
        ('local', 'local', 'local'),
        ('local', 'local', 'remote'),
        ('local', 'remote', 'remote'),
    ],
)
# test simple topology with shards on remote
async def test_pseudo_remote_peas_replicas(gateway, head, worker):
    NUM_REPLICAS = 3
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head pea
    head_pea = _create_head_pea(head, head_port)
    head_pea.start()

    # create the shards
    replica_peas = []
    for i in range(NUM_REPLICAS):
        # create worker
        worker_port = random_port()
        # create a single worker pea
        worker_pea = _create_worker_pea(worker, worker_port, f'pod0/{i}')
        replica_peas.append(worker_pea)
        worker_pea.start()

        await asyncio.sleep(0.1)
        if head == 'remote':
            worker_host = __docker_host__
        else:
            worker_host = HOST

        # this would be done by the Pod, its adding the worker to the head
        activate_msg = ControlRequest(command='ACTIVATE')
        activate_msg.add_related_entity('worker', worker_host, worker_port)
        GrpcConnectionPool.send_request_sync(activate_msg, f'{HOST}:{head_port}')

    # create a single gateway pea
    gateway_pea = _create_gateway_pea(
        gateway, graph_description, pod_addresses, port_expose
    )
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
@pytest.mark.parametrize('gateway', ['local'])
@pytest.mark.parametrize('head', ['local'])
@pytest.mark.parametrize('worker', ['local', 'remote'])
@pytest.mark.parametrize('uses_before', ['local', 'remote'])
@pytest.mark.parametrize('uses_after', ['local', 'remote'])
async def test_pseudo_remote_peas_executor(
    gateway, head, worker, uses_before, uses_after
):
    """
    TODO: head on remote doesn't consider polling args.
    polling is an arg available with pod_parser, which gets removed for remote head pea
    since JinaD removes non-pea args.
    """
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    peas = []

    NUM_SHARDS = 3

    uses_before_port = random_port()
    uses_before_pea = _create_worker_pea(
        uses_before,
        uses_before_port,
        'pod0/uses_before',
        executor='NameChangeExecutor',
        py_modules='executor.py' if is_remote(uses_before) else 'executors/executor.py',
        upload_files=[os.path.join(cur_dir, 'executors')]
        if is_remote(uses_before)
        else None,
    )
    uses_before_pea.start()
    peas.append(uses_before_pea)

    uses_after_port = random_port()
    uses_after_pea = _create_worker_pea(
        uses_after,
        uses_after_port,
        'pod0/uses_after',
        executor='NameChangeExecutor',
        py_modules='executor.py' if is_remote(uses_after) else 'executors/executor.py',
        upload_files=[os.path.join(cur_dir, 'executors')]
        if is_remote(uses_after)
        else None,
    )
    uses_after_pea.start()
    peas.append(uses_after_pea)

    # create head
    head_port = random_port()
    pod_addresses = f'{{"pod0": ["{HOST}:{head_port}"]}}'
    head_pea = _create_head_pea(
        head,
        head_port,
        polling=PollingType.ALL,
        name='pod0/head',
        uses_before=f'{__docker_host__ if is_remote(head) else HOST}:{uses_before_port}',
        uses_after=f'{__docker_host__ if is_remote(head) else HOST}:{uses_after_port}',
    )

    peas.append(head_pea)
    head_pea.start()

    # create some shards
    for i in range(NUM_SHARDS):
        # create worker
        worker_port = random_port()
        print(f'worker_port: {worker_port}')
        worker_pea = _create_worker_pea(
            worker,
            worker_port,
            f'pod0/shards/{i}',
            executor='NameChangeExecutor',
            py_modules='executor.py' if is_remote(worker) else 'executors/executor.py',
            upload_files=[os.path.join(cur_dir, 'executors')]
            if is_remote(worker)
            else None,
        )
        worker_pea.start()
        peas.append(worker_pea)
        await asyncio.sleep(0.1)

        worker_host = HOST
        await _activate_worker(
            head_host=HOST,
            head_port=head_port,
            worker_host=worker_host,
            worker_port=worker_port,
            shard_id=i,
        )

    # create a single gateway pea
    port_expose = random_port()
    gateway_pea = _create_gateway_pea(
        gateway, graph_description, pod_addresses, port_expose
    )
    print(f'head_port: {head_port}, port_expose: {port_expose}')

    gateway_pea.start()
    peas.append(gateway_pea)

    await asyncio.sleep(1.0)

    c = Client(host=HOST, port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response.docs)

    # clean up peas
    for pea in peas:
        pea.close()

    assert len(response_list) == 20
    assert (
        len(response_list[0]) == (1 + 1 + 1) * NUM_SHARDS + 1
    )  # 1 starting doc + 1 uses_before + every exec adds 1 * NUM_SHARDS shards + 1 doc uses_after

    doc_texts = [doc.text for doc in response_list[0]]
    print(doc_texts)
    assert doc_texts.count('client0-Request') == NUM_SHARDS
    assert doc_texts.count('pod0/uses_before') == NUM_SHARDS
    assert doc_texts.count('pod0/uses_after') == 1
    for i in range(NUM_SHARDS):
        assert doc_texts.count(f'pod0/shards/{i}') == 1
