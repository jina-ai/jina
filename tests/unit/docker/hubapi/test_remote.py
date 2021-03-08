import os

import pytest
import requests

from jina.docker.hubapi.remote import _register_to_mongodb
from jina.logging import JinaLogger

DUMMY_ACCESS_TOKEN = 'dummy access'


@pytest.fixture
def dummy_access_token(tmpdir):
    os.mkdir(os.path.join(str(tmpdir), '.jina'))
    access_path = os.path.join(os.path.join(str(tmpdir), '.jina'), 'access.yml')

    with open(access_path, 'w') as wp:
        wp.write(f'access_token: {DUMMY_ACCESS_TOKEN}')


@pytest.mark.parametrize('summary', [None, {'data': True}, {'data': {'subdata': 10.0}}])
@pytest.mark.parametrize(
    'response_code',
    [
        requests.codes.ok,
        requests.codes.unauthorized,
        requests.codes.internal_server_error,
    ],
)
def test_register_to_mongodb(
    dummy_access_token, tmpdir, monkeypatch, mocker, summary, response_code
):
    import json
    from pathlib import Path

    class MockResponse:
        def __init__(self, content):
            self.content = content

        def json(self):
            return self.content

        def status_code(self):
            return response_code

    mock = mocker.Mock()

    def _mock_post(url, headers, data):
        mock(url=url, headers=headers, data=data)
        resp = {'text': f'return status code {response_code}'}
        return MockResponse(resp)

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
