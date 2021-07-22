import pytest
import requests
import aiohttp

from daemon.models.id import DaemonID
from daemon.client.base import BaseClient
from daemon.client.peas import PeaClient, AsyncPeaClient
from daemon.client.pods import PodClient, AsyncPodClient
from daemon.client.flows import FlowClient
from daemon.client.workspaces import WorkspaceClient
from jina.logging.logger import JinaLogger

logger = JinaLogger('BaseTests')
MOCK_URI = '1.2.3.4:7230'


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


@pytest.mark.parametrize(
    'client_cls', [BaseClient, PeaClient, PodClient, FlowClient, WorkspaceClient]
)
@pytest.mark.asyncio
async def test_alive(monkeypatch, client_cls):
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


@pytest.mark.parametrize(
    'client_cls', [BaseClient, PeaClient, PodClient, FlowClient, WorkspaceClient]
)
@pytest.mark.asyncio
async def test_status(monkeypatch, client_cls):
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
@pytest.mark.parametrize(
    'client_cls', [BaseClient, PeaClient, PodClient, FlowClient, WorkspaceClient]
)
@pytest.mark.asyncio
async def test_get(monkeypatch, identity, client_cls):
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


@pytest.mark.parametrize(
    'client_cls', [BaseClient, PeaClient, PodClient, FlowClient, WorkspaceClient]
)
@pytest.mark.asyncio
async def test_list(monkeypatch, client_cls):
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
@pytest.mark.parametrize('client_cls', [AsyncPeaClient, AsyncPodClient])
@pytest.mark.asyncio
async def test_peapod_create(monkeypatch, identity, client_cls):
    payload = {'1': 2}

    client = client_cls(uri=MOCK_URI, logger=logger)
    monkeypatch.setattr(
        aiohttp, 'request', lambda **kwargs: MockAiohttpResponse({1: 2}, 201)
    )
    assert await client.create(identity, payload) == {1: 2}

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert await client.create(identity, payload) is None

    monkeypatch.setattr(
        aiohttp,
        'request',
        lambda **kwargs: MockAiohttpResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 404
        ),
    )
    assert await client.create(identity, payload) is None

    monkeypatch.setattr(aiohttp, 'request', lambda **kwargs: MockAiohttpException())
    assert await client.create(identity, payload) is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jpea'), DaemonID('jpod')],
)
@pytest.mark.parametrize('client_cls', [AsyncPeaClient, AsyncPodClient])
@pytest.mark.asyncio
async def test_peapod_delete(monkeypatch, identity, client_cls):
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
