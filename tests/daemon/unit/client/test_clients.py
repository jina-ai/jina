import pytest
import requests

from daemon.models.id import DaemonID
from daemon.client.base import BaseClient
from daemon.client.peas import _PeaClient
from daemon.client.pods import _PodClient
from daemon.client.flows import _FlowClient
from daemon.client.workspaces import _WorkspaceClient
from jina.logging.logger import JinaLogger

logger = JinaLogger('BaseTests')


class MockResponse:
    def __init__(self, response_json, status_code) -> None:
        self._response_json = response_json
        self._status_code = status_code

    @property
    def status_code(self):
        return self._status_code

    def json(self):
        return self._response_json


class MockRequestsException:
    def __init__(self) -> None:
        raise requests.exceptions.ConnectionError


@pytest.mark.parametrize(
    'client_cls', [BaseClient, _PeaClient, _PodClient, _FlowClient, _WorkspaceClient]
)
def test_alive(monkeypatch, client_cls):
    client = client_cls(uri='1.2.3.4:7230', logger=logger)
    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockResponse('', 200))
    assert client.alive()

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockResponse('', 400))
    assert not client.alive()

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockRequestsException())
    assert not client.alive()


@pytest.mark.parametrize(
    'client_cls', [BaseClient, _PeaClient, _PodClient, _FlowClient, _WorkspaceClient]
)
def test_status(monkeypatch, client_cls):
    client = client_cls(uri='1.2.3.4:7230', logger=logger)
    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockResponse({1: 2}, 200))
    assert client.status() == {1: 2}

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockResponse({1: 2}, 400))
    assert client.status() is None

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockRequestsException())
    assert client.status() is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jworkspace'), DaemonID('jpea'), DaemonID('jpod'), DaemonID('jflow')],
)
@pytest.mark.parametrize(
    'client_cls', [BaseClient, _PeaClient, _PodClient, _FlowClient, _WorkspaceClient]
)
def test_get(monkeypatch, identity, client_cls):
    client = client_cls(uri='1.2.3.4:7230', logger=logger)
    monkeypatch.setattr(
        requests,
        'get',
        lambda **kwargs: MockResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert client.get(identity) == 'empty data'

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockResponse({1: 2}, 200))
    assert client.get(identity) == {1: 2}

    monkeypatch.setattr(
        requests, 'get', lambda **kwargs: MockResponse({'detail': 'client error'}, 404)
    )
    assert client.get(identity) == 'client error'

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockRequestsException())
    assert client.get(identity) is None


@pytest.mark.parametrize(
    'client_cls', [BaseClient, _PeaClient, _PodClient, _FlowClient, _WorkspaceClient]
)
def test_list(monkeypatch, client_cls):
    client = client_cls(uri='1.2.3.4:7230', logger=logger)
    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockResponse({1: 2}, 200))
    assert client.list() == {1: 2}

    monkeypatch.setattr(
        requests, 'get', lambda **kwargs: MockResponse({'items': [5, 6]}, 200)
    )
    assert client.list() == [5, 6]

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockRequestsException())
    assert client.list() is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jpea'), DaemonID('jpod')],
)
@pytest.mark.parametrize('client_cls', [_PeaClient, _PodClient])
def test_peapod_create(monkeypatch, identity, client_cls):
    payload = {'1': 2}

    client = client_cls(uri='1.2.3.4:7230', logger=logger)
    monkeypatch.setattr(requests, 'post', lambda **kwargs: MockResponse({1: 2}, 201))
    assert client.create(identity, payload) == {1: 2}

    monkeypatch.setattr(
        requests,
        'post',
        lambda **kwargs: MockResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert client.create(identity, payload) is None

    monkeypatch.setattr(
        requests,
        'post',
        lambda **kwargs: MockResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 404
        ),
    )
    assert client.create(identity, payload) is None

    monkeypatch.setattr(requests, 'get', lambda **kwargs: MockRequestsException())
    assert client.create(identity, payload) is None


@pytest.mark.parametrize(
    'identity',
    [DaemonID('jpea'), DaemonID('jpod')],
)
@pytest.mark.parametrize('client_cls', [_PeaClient, _PodClient])
def test_peapod_delete(monkeypatch, identity, client_cls):
    client = client_cls(uri='1.2.3.4:7230', logger=logger)
    monkeypatch.setattr(
        requests,
        'delete',
        lambda **kwargs: MockResponse(
            {'detail': [{'msg': 'abcd'}], 'body': 'empty data'}, 422
        ),
    )
    assert not client.delete(identity)

    monkeypatch.setattr(requests, 'delete', lambda **kwargs: MockResponse({1: 2}, 200))
    assert client.delete(identity)

    monkeypatch.setattr(
        requests,
        'delete',
        lambda **kwargs: MockResponse({'detail': 'client error', 'body': 'abc'}, 404),
    )
    assert not client.delete(identity)

    monkeypatch.setattr(requests, 'delete', lambda **kwargs: MockRequestsException())
    assert not client.delete(identity)
