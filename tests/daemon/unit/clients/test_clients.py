import pytest
import aiohttp

from daemon.models.id import DaemonID
from daemon.clients import JinaDClient
from daemon.clients.base import BaseClient, AsyncBaseClient
from daemon.clients.peas import PeaClient, AsyncPeaClient
from daemon.clients.pods import PodClient, AsyncPodClient
from daemon.clients.flows import FlowClient, AsyncFlowClient
from daemon.clients.workspaces import WorkspaceClient, AsyncWorkspaceClient
from jina.logging.logger import JinaLogger

logger = JinaLogger('BaseTests')
MOCK_URI = '1.2.3.4:7230'


all_sync_clients = [BaseClient, PeaClient, PodClient, FlowClient, WorkspaceClient]
all_async_clients = [
    AsyncBaseClient,
    AsyncPeaClient,
    AsyncPodClient,
    AsyncFlowClient,
    AsyncWorkspaceClient,
]


class MockAiohttpResponse:
    def __init__(self, response_json, status) -> None:
        self._response_json = response_json
        self._status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        return

    @property
    def status(self):
        return self._status

    async def json(self):
        return self._response_json


class MockAiohttpException:
    def __init__(self) -> None:
        raise aiohttp.ClientConnectionError


@pytest.mark.parametrize('client_cls', all_sync_clients)
def test_alive(monkeypatch, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse('', 200)
    )
    assert client.alive()

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse('', 400)
    )
    assert not client.alive()

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert not client.alive()


@pytest.mark.parametrize('client_cls', all_async_clients)
@pytest.mark.asyncio
async def test_alive_async(monkeypatch, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse('', 200)
    )
    assert await client.alive()

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse('', 400)
    )
    assert not await client.alive()

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert not await client.alive()


@pytest.mark.parametrize('client_cls', all_sync_clients)
def test_status(monkeypatch, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert client.status() == {1: 2}

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 400)
    )
    assert client.status() is None

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert client.status() is None


@pytest.mark.parametrize('client_cls', all_async_clients)
@pytest.mark.asyncio
async def test_status_async(monkeypatch, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert await client.status() == {1: 2}

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 400)
    )
    assert await client.status() is None

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert await client.status() is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jworkspace'), DaemonID('jpea'), DaemonID('jpod'), DaemonID('jflow')],
)
@pytest.mark.parametrize('client_cls', all_sync_clients)
def test_get(monkeypatch, identity, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert client.get(identity) == 'empty data'

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert client.get(identity) == {1: 2}

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse({'detail': 'client error'}, 404),
    )
    assert client.get(identity) == 'client error'

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert client.get(identity) is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jworkspace'), DaemonID('jpea'), DaemonID('jpod'), DaemonID('jflow')],
)
@pytest.mark.parametrize('client_cls', all_async_clients)
@pytest.mark.asyncio
async def test_get_async(monkeypatch, identity, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert await client.get(identity) == 'empty data'

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert await client.get(identity) == {1: 2}

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse({'detail': 'client error'}, 404),
    )
    assert await client.get(identity) == 'client error'

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert await client.get(identity) is None


@pytest.mark.parametrize('client_cls', all_sync_clients)
def test_list(monkeypatch, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert client.list() == {1: 2}

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({'items': [5, 6]}, 200)
    )
    assert client.list() == [5, 6]

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert client.list() is None


@pytest.mark.parametrize('client_cls', all_async_clients)
@pytest.mark.asyncio
async def test_list_async(monkeypatch, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert await client.list() == {1: 2}

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({'items': [5, 6]}, 200)
    )
    assert await client.list() == [5, 6]

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert await client.list() is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jpea'), DaemonID('jpod')],
)
@pytest.mark.parametrize('client_cls', [PeaClient, PodClient])
def test_peapod_create(monkeypatch, identity, client_cls):
    payload = {'1': 2}

    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 201)
    )
    status, response = client.create(identity, payload)
    assert status
    assert response == {1: 2}

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    status, response = client.create(identity, payload)
    assert not status
    assert response == 'validation error in the payload: abcd'

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': ['empty', 'data']}, 404
        ),
    )
    status, response = client.create(identity, payload)
    assert not status
    assert response == 'empty\ndata'

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert client.create(identity, payload) is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jpea'), DaemonID('jpod')],
)
@pytest.mark.parametrize('client_cls', [AsyncPeaClient, AsyncPodClient])
@pytest.mark.asyncio
async def test_peapod_create_async(monkeypatch, identity, client_cls):
    payload = {'1': 2}

    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 201)
    )
    status, response = await client.create(identity, payload)
    assert status
    assert response == {1: 2}

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    status, response = await client.create(identity, payload)
    assert not status
    assert response == 'validation error in the payload: abcd'

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': ['empty', 'data']}, 404
        ),
    )
    status, response = await client.create(identity, payload)
    assert not status
    assert response == 'empty\ndata'

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert await client.create(identity, payload) is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jpea'), DaemonID('jpod')],
)
@pytest.mark.parametrize('client_cls', [PeaClient, PodClient])
def test_peapod_delete(monkeypatch, identity, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert not client.delete(identity)

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert client.delete(identity)

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': 'client error', 'body': 'abc'}, 404
        ),
    )
    assert not client.delete(identity)

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert not client.delete(identity)


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jpea'), DaemonID('jpod')],
)
@pytest.mark.parametrize('client_cls', [AsyncPeaClient, AsyncPodClient])
@pytest.mark.asyncio
async def test_peapod_delete_async(monkeypatch, identity, client_cls):
    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert not await client.delete(identity)

    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 200)
    )
    assert await client.delete(identity)

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': 'client error', 'body': 'abc'}, 404
        ),
    )
    assert not await client.delete(identity)

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert not await client.delete(identity)


def test_timeout():
    client = JinaDClient(host='1.2.3.4', port=8000)
    assert client.peas.timeout.total == 10 * 60

    client = JinaDClient(host='1.2.3.4', port=8000, timeout=10)
    assert client.peas.timeout.total == 10
