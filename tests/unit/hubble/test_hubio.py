import os
import json
import pytest
import requests

from jina.hubble.hubio import HubIO
from jina.parsers.hubble import set_hub_push_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MockResponse:
    def __init__(self, response_code: int = 201):
        self.response_code = response_code

    def json(self):
        return {
            'code': 0,
            'success': True,
            'data': {
                'images': [
                    {
                        'id': 'w7qckiqy',
                        'secret': 'f7386f9ef7ea238fd955f2de9fb254a0',
                        'pullPath': 'jinahub/w7qckiqy:v3',
                    }
                ]
            },
            'message': 'uploaded successfully',
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
def test_push(mocker, monkeypatch, path, mode):
    mock = mocker.Mock()

    def _mock_post(url, files, data):
        mock(url=url, files=files, data=data)
        return MockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    args = set_hub_push_parser().parse_args(_args_list)
    result = HubIO(args).push()
