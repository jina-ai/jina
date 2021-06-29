import os
import json
import pytest
import requests

from jina.hubble.hubio import HubIO
from jina.parsers.hubble import set_hub_push_parser
from jina.parsers.hubble import set_hub_pull_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


class PostMockResponse:
    def __init__(self, response_code: int = 201):
        self.response_code = response_code

    def json(self):
        return {
            'code': 0,
            'success': True,
            'executors': [
                {
                    'id': 'w7qckiqy',
                    'secret': 'f7386f9ef7ea238fd955f2de9fb254a0',
                    'image': 'jinahub/w7qckiqy:v3',
                    'visibility': 'public',
                }
            ],
            'message': 'uploaded successfully',
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


class GetMockResponse:
    def __init__(self, response_code: int = 201):
        self.response_code = response_code

    def json(self):
        return {
            'keywords': [],
            'id': 'dummy_mwu_encoder',
            'alias': 'alias_dummy',
            'tag': 'v0',
            'versions': [],
            'visibility': 'public',
            'image': 'jinahub/pod.dummy_mwu_encoder',
            'package': {
                'download': 'http://hubbleapi.jina.ai/files/dummy_mwu_encoder-v0.zip',
                'md5': 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f',
            },
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

    def _mock_post(url, files, data, headers=None):
        mock(url=url, files=files, data=data)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    args = set_hub_push_parser().parse_args(_args_list)
    result = HubIO(args).push()


def test_fetch(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_get(url, headers=None):
        mock(url=url)
        return GetMockResponse(response_code=requests.codes.ok)

    monkeypatch.setattr(requests, 'get', _mock_get)
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    executor = HubIO(args).fetch('dummy_mwu_encoder')

    assert executor.uuid == 'dummy_mwu_encoder'
    assert executor.alias == 'alias_dummy'
    assert executor.tag == 'v0'
    assert executor.image_name == 'jinahub/pod.dummy_mwu_encoder'
    assert executor.md5sum == 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f'


def test_pull(mocker, monkeypatch):
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    HubIO(args).pull()

    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder:secret'])

    HubIO(args).pull()
