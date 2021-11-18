import threading
import multiprocessing

import pytest

from daemon.clients import JinaDClient, AsyncJinaDClient
from daemon.models.id import DaemonID
from jina.peapods.peas.helper import is_ready
from jina.peapods.peas.jinad import JinaDPea, JinaDProcessTarget
from jina.enums import replace_enum_to_str
from jina.parsers import set_pea_parser

HOST = '127.0.0.1'


@pytest.mark.asyncio
async def test_async_jinad_client():
    args = set_pea_parser().parse_args([])

    client = AsyncJinaDClient(host=HOST, port=8000)
    workspace_id = await client.workspaces.create(
        paths=[], id=args.workspace_id, complete=True
    )
    assert DaemonID(workspace_id)
    payload = replace_enum_to_str(vars(args))
    assert not is_ready(f'{HOST}:{args.port_in}')

    success, response = await client.peas.create(
        workspace_id=workspace_id, payload=payload
    )
    assert success
    pea_id = DaemonID(response)

    assert is_ready(f'{HOST}:{args.port_in}')
    assert await client.peas.delete(pea_id)
    assert not is_ready(f'{HOST}:{args.port_in}')


def test_sync_jinad_client():
    args = set_pea_parser().parse_args([])

    client = JinaDClient(host=HOST, port=8000)
    workspace_id = client.workspaces.create(
        paths=[], id=args.workspace_id, complete=True
    )
    assert DaemonID(workspace_id)
    payload = replace_enum_to_str(vars(args))
    assert not is_ready(f'{HOST}:{args.port_in}')

    success, response = client.peas.create(workspace_id=workspace_id, payload=payload)
    assert success
    pea_id = DaemonID(response)

    assert is_ready(f'{HOST}:{args.port_in}')
    assert client.peas.delete(pea_id)
    assert not is_ready(f'{HOST}:{args.port_in}')


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
    assert is_ready(f'{HOST}:{args.port_in}')
    process.join()
    assert is_shutdown_event.is_set()
    assert not is_ready(f'{HOST}:{args.port_in}')


@pytest.mark.parametrize('runtime_backend', ['PROCESS', 'THREAD'])
def test_jinad_pea(runtime_backend):
    args = set_pea_parser().parse_args(['--runtime-backend', runtime_backend])

    assert not is_ready(f'{HOST}:{args.port_in}')
    with JinaDPea(args):
        assert is_ready(f'{HOST}:{args.port_in}')
    assert not is_ready(f'{HOST}:{args.port_in}')
