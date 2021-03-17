import os

import pytest

from jina.docker.hubio import HubIO
from jina.parsers.hub import (
    set_hub_new_parser,
    set_hub_pushpull_parser,
    set_hub_build_parser,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('new_type', ['pod', 'app', 'template'])
def test_create_new(tmpdir, new_type):
    args = set_hub_new_parser().parse_args(
        ['--output-dir', str(tmpdir), '--type', new_type]
    )
    HubIO(args).new(no_input=True)
    list_dir = os.listdir(str(tmpdir))
    assert len(list_dir) == 1


def test_login(tmpdir, monkeypatch, mocker):
    import requests
    import webbrowser
    from pathlib import Path

    class MockResponse:
        def __init__(self, content):
            self.content = content

        def json(self):
            return self.content

        def status_code(self):
            return requests.codes.ok

    mock = mocker.Mock()

    def _mock_post(url, headers, data):
        mock(url=url, headers=headers, data=data)
        resp = {
            'device_code': 'device',
            'user_code': 'user',
            'verification_uri': 'verification',
            'access_token': 'access',
        }
        return MockResponse(resp)

    def _mock_home():
        return Path(str(tmpdir))

    args = set_hub_pushpull_parser()
    monkeypatch.setattr(requests, 'post', _mock_post)
    monkeypatch.setattr(webbrowser, 'open', None)
    monkeypatch.setattr(Path, 'home', _mock_home)
    HubIO(args).login()
    device_request_kwargs = mock.call_args_list[0][1]
    assert device_request_kwargs['url'] == 'https://github.com/login/device/code'
    assert device_request_kwargs['headers'] == {'Accept': 'application/json'}
    assert 'client_id' in device_request_kwargs['data']
    assert 'scope' in device_request_kwargs['data']

    access_request_kwargs = mock.call_args_list[1][1]
    assert access_request_kwargs['url'] == 'https://github.com/login/oauth/access_token'
    assert access_request_kwargs['headers'] == {'Accept': 'application/json'}
    assert 'client_id' in access_request_kwargs['data']
    assert 'device_code' in access_request_kwargs['data']
    assert access_request_kwargs['data']['device_code'] == 'device'

    list_dir = os.listdir(str(tmpdir))
    assert '.jina' in list_dir
    jina_subfolder = os.path.join(str(tmpdir), '.jina')
    assert Path(os.path.join(jina_subfolder, 'access.yml')).exists()
    with open(os.path.join(jina_subfolder, 'access.yml')) as fp:
        assert fp.read() == 'access_token: access\n'


@pytest.mark.parametrize('dockerfile', ['', 'Dockerfile', 'another.Dockerfile'])
@pytest.mark.parametrize('argument', ['--file', '-f'])
def test_dry_run(dockerfile, argument):
    hub_mwu_path = os.path.join(cur_dir, 'hub-mwu')
    _args_list = [hub_mwu_path, '--dry-run']
    if dockerfile:
        _args_list += [argument, dockerfile]
    args = set_hub_build_parser().parse_args(_args_list)
    result = HubIO(args).build()
    assert result['Dockerfile'] == os.path.join(
        hub_mwu_path, dockerfile if dockerfile else 'Dockerfile'
    )
    assert result['manifest.yml'] == os.path.join(hub_mwu_path, 'manifest.yml')
    assert result['config.yml'] == os.path.join(hub_mwu_path, 'mwu_encoder.yml')
    assert result['README.md'] == os.path.join(hub_mwu_path, 'README.md')
