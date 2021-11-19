import asyncio
import threading
import multiprocessing

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient
from daemon.models.id import DaemonID

from jina.helper import random_port
from jina import Document, Client, __docker_host__
from jina.enums import PollingType, PeaRoleType
from jina.peapods.peas.factory import PeaFactory
from jina.peapods.peas.helper import is_ready
from jina.peapods.peas.jinad import JinaDPea, JinaDProcessTarget
from jina.enums import replace_enum_to_str
from jina.types.message.common import ControlMessage
from jina.parsers import set_pea_parser, set_gateway_parser
from jina.peapods.networking import GrpcConnectionPool

HOST = '127.0.0.1'
PORT_JINAD = 8000


def is_pea_ready(args):
    return is_ready(f'{HOST}:{args.port_in}')


@pytest.mark.asyncio
async def test_async_jinad_client():
    args = set_pea_parser().parse_args([])

    client = AsyncJinaDClient(host=HOST, port=PORT_JINAD)
    workspace_id = await client.workspaces.create(
        paths=[], id=args.workspace_id, complete=True
    )
    assert DaemonID(workspace_id)
    payload = replace_enum_to_str(vars(args))
    assert not is_pea_ready(args)

    success, response = await client.peas.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success
    pea_id = DaemonID(response)

    assert is_pea_ready(args)
    assert await client.peas.delete(pea_id)
    assert not is_pea_ready(args)


def test_sync_jinad_client():
    args = set_pea_parser().parse_args([])

    client = JinaDClient(host=HOST, port=8000)
    workspace_id = client.workspaces.create(
        paths=[], id=args.workspace_id, complete=True
    )
    assert DaemonID(workspace_id)
    payload = replace_enum_to_str(vars(args))
    assert not is_pea_ready(args)

    success, response = client.peas.create(workspace_id=workspace_id, payload=payload)
    assert success
    pea_id = DaemonID(response)

    assert is_pea_ready(args)
    assert client.peas.delete(pea_id)
    assert not is_pea_ready(args)


@pytest.mark.parametrize(
    'worker_cls, event',
    [
        (multiprocessing.Process, multiprocessing.Event),
        (threading.Thread, threading.Event),
    ],
)
def test_jinad_process_target(worker_cls, event):
    is_started_event, is_shutdown_event, is_ready_event, is_cancelled_event = [
        event()
    ] * 4
    args = set_pea_parser().parse_args([])

    process = worker_cls(
        target=JinaDProcessTarget(),
        kwargs={
            'args': args,
            'is_started': is_started_event,
            'is_shutdown': is_shutdown_event,
            'is_ready': is_ready_event,
            'is_cancelled': is_cancelled_event,
        },
    )
    process.start()
    is_ready_event.wait()
    assert is_pea_ready(args)
    process.join()
    assert is_shutdown_event.is_set()
    assert not is_pea_ready(args)


@pytest.mark.parametrize('runtime_backend', ['PROCESS', 'THREAD'])
def test_jinad_pea(runtime_backend):
    args = set_pea_parser().parse_args(['--runtime-backend', runtime_backend])
    assert not is_pea_ready(args)

    with JinaDPea(args):
        assert is_pea_ready(args)
    assert not is_pea_ready(args)


def _create_worker_pea(l_or_r, port):
    args = set_pea_parser().parse_args([])
    if l_or_r == 'remote':
        args.host = HOST
        args.port_jinad = PORT_JINAD
    args.name = f'worker-{l_or_r}'
    args.port_in = port
    args.runtime_cls = 'WorkerRuntime'
    return PeaFactory.build_pea(args)


def _create_head_pea(l_or_r, port):
    args = set_pea_parser().parse_args([])
    if l_or_r == 'remote':
        args.host = HOST
        args.port_jinad = PORT_JINAD
    args.name = f'head-{l_or_r}'
    args.port_in = port
    args.pea_role = PeaRoleType.HEAD
    args.polling = PollingType.ANY
    args.runtime_cls = 'HeadRuntime'
    return PeaFactory.build_pea(args)


def _create_gateway_pea(l_or_r, graph_description, pods_addresses, port_expose):
    args = set_gateway_parser().parse_args([])
    if l_or_r == 'remote':
        args.host = HOST
        args.port_jinad = PORT_JINAD
    args.graph_description = graph_description
    args.pods_addresses = pods_addresses
    args.port_expose = port_expose
    args.runtime_cls = 'GRPCGatewayRuntime'
    return PeaFactory.build_pea(args)


async def async_inputs():
    for i in range(20):
        yield Document(text=f'client{i}-Request')


@pytest.mark.asyncio
@pytest.mark.parametrize('gateway', ['local'])
@pytest.mark.parametrize('head', ['local', 'remote'])
@pytest.mark.parametrize('worker', ['local', 'remote'])
async def test_psuedo_remote_peas_topologies(gateway, head, worker):
    """
    TODO: current status
    g(l)-h(l)-w(l) - works
    g(l)-h(l)-w(r) - works - head connects to worker via localhost
    g(l)-h(r)-w(l) - works - head (inside docker) connects to worker via dockerhost
    g(l)-h(r)-w(r) - works - head (inside docker) connects to worker via dockerhost
    g(r)-... - doesn't work, as distributed parser not enabled for gateway
    After any 1 failure, segfault
    """
    worker_port = random_port()
    head_port = random_port()
    port_expose = random_port()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
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
        activate_msg = ControlMessage(command='ACTIVATE')
        worker_host, worker_port = worker_pea.runtime_ctrl_address.split(':')
        if head == 'remote':
            worker_host = __docker_host__

        activate_msg.add_related_entity('worker', worker_host, int(worker_port))
        assert GrpcConnectionPool.send_message_sync(
            activate_msg, head_pea.runtime_ctrl_address
        )

        # send requests to the gateway
        c = Client(host='localhost', port=port_expose, asyncio=True)
        responses = c.post(
            '/', inputs=async_inputs, request_size=1, return_results=True
        )
        response_list = []
        async for response in responses:
            response_list.append(response)

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1
