import os
import json
import base64
from pathlib import Path

import pytest
import requests

from jina.docker.hubapi.remote import _register_to_mongodb, _fetch_docker_auth
from jina.logging.logger import JinaLogger
from jina.excepts import HubLoginRequired

DUMMY_ACCESS_TOKEN = 'dummy access'


@pytest.fixture
def dummy_access_token(tmpdir):
    os.mkdir(os.path.join(str(tmpdir), '.jina'))
    access_path = os.path.join(os.path.join(str(tmpdir), '.jina'), 'access.yml')

    with open(access_path, 'w') as wp:
        wp.write(f'access_token: {DUMMY_ACCESS_TOKEN}')


class MockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    @property
    def text(self):
        return json.dumps(
            {
                'docker_username': base64.b64encode('abc'.encode('ascii')).decode(
                    'ascii'
                ),
                'docker_password': base64.b64encode('def'.encode('ascii')).decode(
                    'ascii'
                ),
            }
        )

    @property
    def status_code(self):
        return self.response_code


def test_docker_auth_success(mocker, dummy_access_token, monkeypatch, tmpdir):
    mock = mocker.Mock()

    def _mock_get(url, headers):
        mock(url=url, headers=headers)
        return MockResponse(response_code=requests.codes.ok)

    def _mock_home():
        return Path(str(tmpdir))

    monkeypatch.setattr(requests, 'get', _mock_get)
    monkeypatch.setattr(Path, 'home', _mock_home)

    username, password = _fetch_docker_auth(logger=JinaLogger('test_docker_auth'))
    assert username == 'abc'
    assert password == 'def'


def test_docker_auth_failure(mocker, dummy_access_token, monkeypatch, tmpdir):
    mock = mocker.Mock()

    def _mock_get(url, headers):
        mock(url=url, headers=headers)
        return MockResponse(response_code=requests.codes.unauthorized)

    def _mock_home():
        return Path(str(tmpdir))

    monkeypatch.setattr(requests, 'get', _mock_get)
    monkeypatch.setattr(Path, 'home', _mock_home)

    with pytest.raises(HubLoginRequired):
        _fetch_docker_auth(logger=JinaLogger('test_docker_auth'))


@pytest.mark.parametrize('summary', [{'data': True}, {'data': {'subdata': 10.0}}])
def test_register_to_mongodb_success(
    dummy_access_token, tmpdir, monkeypatch, mocker, summary
):
    mock = mocker.Mock()

    def _mock_post(url, headers, data):
        mock(url=url, headers=headers, data=data)
        return MockResponse(response_code=requests.codes.ok)

    def _mock_home():
        return Path(str(tmpdir))

    monkeypatch.setattr(requests, 'post', _mock_post)
    monkeypatch.setattr(Path, 'home', _mock_home)
    _register_to_mongodb(JinaLogger('test_mongodb_register'), summary)

    request_args = mock.call_args_list[0][1]
    assert request_args['url'] == 'https://hubapi.jina.ai/push'
    assert request_args['headers'] == {
        'Accept': 'application/json',
        'authorizationToken': f'{DUMMY_ACCESS_TOKEN}',
    }
    assert request_args['data'] == json.dumps(summary)


@pytest.mark.parametrize('summary', [None, {'data': True}, {'data': {'subdata': 10.0}}])
@pytest.mark.parametrize(
    'response_code',
    [
        requests.codes.unauthorized,
        requests.codes.internal_server_error,
    ],
)
def test_register_to_mongodb_failure(
    dummy_access_token, tmpdir, monkeypatch, mocker, summary, response_code
):
    mock = mocker.Mock()

    def _mock_post(url, headers, data):
        mock(url=url, headers=headers, data=data)
        return MockResponse(response_code=response_code)

    def _mock_home():
        return Path(str(tmpdir))

    monkeypatch.setattr(requests, 'post', _mock_post)
    monkeypatch.setattr(Path, 'home', _mock_home)
    with pytest.raises(HubLoginRequired):
        _register_to_mongodb(JinaLogger('test_mongodb_register'), summary)
