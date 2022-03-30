import itertools
import json
import os
import shutil
import urllib
from argparse import Namespace
from pathlib import Path

import docker
import pytest
import requests
import yaml

from jina.hubble.helper import disk_cache_offline
from jina.hubble.hubio import HubExecutor, HubIO
from jina.parsers.hubble import (
    set_hub_new_parser,
    set_hub_pull_parser,
    set_hub_push_parser,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))


class PostMockResponse:
    def __init__(self, response_code: int = 201):
        self.response_code = response_code

    def json(self):
        return {
            'type': 'complete',
            'subject': 'createExecutor',
            'message': 'Successfully pushed w7qckiqy',
            'payload': {
                'id': 'w7qckiqy',
                'secret': 'f7386f9ef7ea238fd955f2de9fb254a0',
                'visibility': 'public',
            },
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code

    def iter_lines(self):
        logs = [
            '{"type":"init","subject":"createExecutor"}',
            '{"type":"start","subject":"extractZip"}',
            '{"type":"done","subject":"extractZip"}',
            '{"type":"start","subject":"pushImage"}',
            '{"type":"done","subject":"pushImage"}',
            '{"type":"complete","subject":"createExecutor","message":"Successfully pushed w7qckiqy","payload":{"id":"w7qckiqy","secret":"f7386f9ef7ea238fd955f2de9fb254a0","visibility":"public"}}',
        ]

        return itertools.chain(logs)


class FetchMetaMockResponse:
    def __init__(self, response_code: int = 200, no_image=False, fail_count=0):
        self.response_code = response_code
        self.no_image = no_image
        self._tried_count = 0
        self._fail_count = fail_count

    def json(self):
        if self._tried_count <= self._fail_count:
            return {'message': 'Internal server error'}

        return {
            'data': {
                'keywords': [],
                'id': 'dummy_mwu_encoder',
                'name': 'alias_dummy',
                'visibility': 'public',
                'commit': {'_id': 'commit_id', 'tags': ['v0']},
                'package': {
                    'containers': []
                    if self.no_image
                    else ['jinahub/pod.dummy_mwu_encoder'],
                    'download': 'http://hubbleapi.jina.ai/files/dummy_mwu_encoder-v0.zip',
                    'md5': 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f',
                },
            }
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        self._tried_count += 1
        if self._tried_count <= self._fail_count:
            return 500

        return self.response_code


@pytest.mark.parametrize('tag', [None, '-t v0'])
@pytest.mark.parametrize('force', [None, 'UUID8'])
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
def test_push(mocker, monkeypatch, path, mode, tmpdir, force, tag):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]
    if force:
        _args_list.extend(['--force', force])

    if tag:
        _args_list.append(tag)

    args = set_hub_push_parser().parse_args(_args_list)
    result = HubIO(args).push()

    # remove .jina
    exec_config_path = os.path.join(exec_path, '.jina')
    shutil.rmtree(exec_config_path)


@pytest.mark.parametrize(
    'dockerfile, expected_error',
    [
        ('Dockerfile', 'The given Dockerfile `{dockerfile}` does not exist!'),
        (
            '../Dockerfile',
            'The Dockerfile must be placed at the given folder `{work_path}`',
        ),
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
def test_push_wrong_dockerfile(
    mocker, monkeypatch, path, mode, tmpdir, dockerfile, expected_error
):
    dockerfile = os.path.join(cur_dir, path, dockerfile)
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    args = set_hub_push_parser().parse_args(_args_list)
    args.dockerfile = dockerfile
    with pytest.raises(Exception) as info:
        HubIO(args).push()

    assert expected_error.format(dockerfile=dockerfile, work_path=args.path) in str(
        info.value
    )


def test_fetch(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return FetchMetaMockResponse(response_code=200)

    monkeypatch.setattr(requests, 'post', _mock_post)
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', None, force=True)

    assert executor.uuid == 'dummy_mwu_encoder'
    assert executor.name == 'alias_dummy'
    assert executor.tag == 'v0'
    assert executor.image_name == 'jinahub/pod.dummy_mwu_encoder'
    assert executor.md5sum == 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f'

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', '', force=True)
    assert executor.tag == 'v0'

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', 'v0.1', force=True)
    assert executor.tag == 'v0.1'


def test_fetch_with_no_image(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return FetchMetaMockResponse(response_code=200, no_image=True)

    monkeypatch.setattr(requests, 'post', _mock_post)

    with pytest.raises(Exception) as exc_info:
        HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert exc_info.match('No image found for executor "dummy_mwu_encoder"')

    executor, _ = HubIO.fetch_meta(
        'dummy_mwu_encoder', tag=None, image_required=False, force=True
    )

    assert executor.image_name is None
    assert mock.call_count == 2


def test_fetch_with_retry(mocker, monkeypatch):
    mock = mocker.Mock()
    mock_response = FetchMetaMockResponse(response_code=200, fail_count=3)

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return mock_response

    monkeypatch.setattr(requests, 'post', _mock_post)

    with pytest.raises(Exception) as exc_info:
        # failing 3 times, so it should raise an error
        HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert exc_info.match('{"message": "Internal server error"}')

    mock_response = FetchMetaMockResponse(response_code=200, fail_count=2)

    # failing 2 times, it must succeed on 3rd time
    executor, _ = HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)
    assert executor.uuid == 'dummy_mwu_encoder'

    assert mock.call_count == 6  # mock must be called 3+3


class DownloadMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def iter_content(self, buffer=32 * 1024):
        zip_file = Path(__file__).parent / 'dummy_executor.zip'
        with zip_file.open('rb') as f:
            yield f.read(buffer)

    @property
    def status_code(self):
        return self.response_code


def test_pull(test_envs, mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_fetch(name, tag=None, secret=None, image_required=True, force=False):
        mock(name=name)
        return (
            HubExecutor(
                uuid='dummy_mwu_encoder',
                name='alias_dummy',
                tag='v0',
                image_name='jinahub/pod.dummy_mwu_encoder',
                md5sum=None,
                visibility=True,
                archive_url=None,
            ),
            False,
        )

    monkeypatch.setattr(HubIO, 'fetch_meta', _mock_fetch)

    def _mock_download(url, stream=True, headers=None):
        mock(url=url)
        return DownloadMockResponse(response_code=200)

    def _mock_head(url):
        from collections import namedtuple

        HeadInfo = namedtuple('HeadInfo', ['headers'])
        return HeadInfo(headers={})

    monkeypatch.setattr(requests, 'get', _mock_download)
    monkeypatch.setattr(requests, 'head', _mock_head)

    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])
    HubIO(args).pull()

    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder:secret'])
    HubIO(args).pull()


class MockDockerClient:
    def __init__(self, fail_pull: bool = True):
        self.fail_pull = fail_pull
        if not self.fail_pull:
            self.images = {}

    def pull(self, repository: str, stream: bool = True, decode: bool = True):
        if self.fail_pull:
            raise docker.errors.APIError('Failed pulling docker image')
        else:
            yield {}


def test_offline_pull(test_envs, mocker, monkeypatch, tmpfile):
    mock = mocker.Mock()

    fail_meta_fetch = True
    version = 'v0'

    @disk_cache_offline(cache_file=str(tmpfile))
    def _mock_fetch(name, tag=None, secret=None, image_required=True, force=False):
        mock(name=name)
        if fail_meta_fetch:
            raise urllib.error.URLError('Failed fetching meta')
        else:
            return HubExecutor(
                uuid='dummy_mwu_encoder',
                name='alias_dummy',
                tag='v0',
                image_name=f'jinahub/pod.dummy_mwu_encoder:{version}',
                md5sum=None,
                visibility=True,
                archive_url=None,
            )

    def _gen_load_docker_client(fail_pull: bool):
        def _load_docker_client(obj):
            obj._raw_client = MockDockerClient(fail_pull=fail_pull)
            obj._client = MockDockerClient(fail_pull=fail_pull)

        return _load_docker_client

    args = set_hub_pull_parser().parse_args(
        ['--force', 'jinahub+docker://dummy_mwu_encoder']
    )
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=True)
    )
    monkeypatch.setattr(HubIO, 'fetch_meta', _mock_fetch)

    # Expect failure due to fetch_meta
    with pytest.raises(urllib.error.URLError):
        HubIO(args).pull()

    fail_meta_fetch = False
    # Expect failure due to image pull
    with pytest.raises(AttributeError):
        HubIO(args).pull()

    # expect successful pull
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=False)
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v0'

    version = 'v1'
    # expect successful forced pull because force == True
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'

    # expect successful pull using cached fetch_meta response and saved image
    fail_meta_fetch = True
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=False)
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'

    args.force_update = False
    fail_meta_fetch = False
    version = 'v2'
    # expect successful but outdated pull because force == False
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'


def test_pull_with_progress():
    import json

    args = set_hub_pull_parser().parse_args(['jinahub+docker://dummy_mwu_encoder'])

    def _log_stream_generator():
        with open(os.path.join(cur_dir, 'docker_pull.logs')) as fin:
            for line in fin:
                if line.strip():
                    yield json.loads(line)

    from rich.console import Console

    console = Console()
    HubIO(args)._pull_with_progress(_log_stream_generator(), console)


@pytest.mark.parametrize('add_dockerfile', [True, False])
def test_new_without_arguments(monkeypatch, tmpdir, add_dockerfile):
    from rich.prompt import Confirm, Prompt

    prompts = iter(
        [
            'DummyExecutor',
            tmpdir / 'DummyExecutor',
            'dummy description',
            'dummy author',
            'dummy tags',
        ]
    )

    confirms = iter([True, add_dockerfile])

    def _mock_prompt_ask(*args, **kwargs):
        return next(prompts)

    def _mock_confirm_ask(*args, **kwargs):
        return next(confirms)

    monkeypatch.setattr(Prompt, 'ask', _mock_prompt_ask)
    monkeypatch.setattr(Confirm, 'ask', _mock_confirm_ask)

    args = set_hub_new_parser().parse_args([])
    HubIO(args).new()
    path = tmpdir / 'DummyExecutor'

    pkg_files = [
        'executor.py',
        'manifest.yml',
        'README.md',
        'requirements.txt',
        'config.yml',
    ]

    if add_dockerfile:
        pkg_files.append('Dockerfile')

    for file in pkg_files:
        assert (path / file).exists()
    for file in [
        'executor.py',
        'manifest.yml',
        'README.md',
        'config.yml',
    ]:
        with open(path / file, 'r') as fp:
            assert 'DummyExecutor' in fp.read()


@pytest.mark.parametrize('add_dockerfile', [True, False])
@pytest.mark.parametrize('advance_configuration', [True, False])
@pytest.mark.parametrize('confirm_advance_configuration', [True, False])
@pytest.mark.parametrize('confirm_add_docker', [True, False])
def test_new_with_arguments(
    monkeypatch,
    tmpdir,
    add_dockerfile,
    advance_configuration,
    confirm_advance_configuration,
    confirm_add_docker,
):
    from rich.prompt import Confirm

    path = os.path.join(tmpdir, 'DummyExecutor')

    _args_list = [
        '--name',
        'argsExecutor',
        '--description',
        'args description',
        '--keywords',
        'args,keywords',
        '--url',
        'args url',
    ]
    temp = []
    _args_list.extend(['--path', path])
    if advance_configuration:
        _args_list.append('--advance-configuration')
    else:
        temp.append(confirm_advance_configuration)

    if add_dockerfile:
        _args_list.append('--add-dockerfile')
    else:
        temp.append(confirm_add_docker)

    confirms = iter(temp)

    def _mock_confirm_ask(*args, **kwargs):
        return next(confirms)

    monkeypatch.setattr(Confirm, 'ask', _mock_confirm_ask)

    args = set_hub_new_parser().parse_args(_args_list)

    HubIO(args).new()
    # path = tmpdir / 'argsExecutor'

    pkg_files = [
        'executor.py',
        'manifest.yml',
        'README.md',
        'requirements.txt',
        'config.yml',
    ]

    path = tmpdir / 'DummyExecutor'
    if (advance_configuration or confirm_advance_configuration) and (
        add_dockerfile or confirm_add_docker
    ):
        pkg_files.append('Dockerfile')

    for file in pkg_files:
        assert (path / file).exists()

    for file in ['executor.py', 'manifest.yml', 'README.md', 'config.yml']:
        with open(path / file, 'r') as fp:
            assert 'argsExecutor' in fp.read()
    if advance_configuration or confirm_advance_configuration:
        with open(path / 'manifest.yml') as fp:
            temp = yaml.load(fp, Loader=yaml.FullLoader)
            assert temp['name'] == 'argsExecutor'
            assert temp['description'] == 'args description'
            assert temp['keywords'] == ['args', 'keywords']
            assert temp['url'] == 'args url'


class SandboxGetMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def json(self):
        if self.response_code == 200:
            return {
                'code': self.response_code,
                'data': {'host': 'http://test_existing_deployment.com', 'port': 4321},
            }
        else:
            return {'code': self.response_code}

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


class SandboxCreateMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def json(self):
        return {
            'code': self.response_code,
            'data': {'host': 'http://test_new_deployment.com', 'port': 4322},
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


def test_deploy_public_sandbox_existing(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return SandboxGetMockResponse(response_code=200)

    monkeypatch.setattr(requests, "post", _mock_post)

    args = Namespace(
        uses='jinahub+sandbox://dummy_mwu_encoder',
        uses_with={'foo': 'bar'},
        test_string='text',
        test_number=1,
    )
    host, port = HubIO.deploy_public_sandbox(args)
    assert host == 'http://test_existing_deployment.com'
    assert port == 4321

    _, kwargs = mock.call_args
    assert kwargs['json']['args'] == {
        'uses_with': {'foo': 'bar'},
        'test_number': 1,
        'test_string': 'text',
    }


def test_deploy_public_sandbox_create_new(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        if url.endswith('/sandbox.get'):
            return SandboxGetMockResponse(response_code=404)
        else:
            return SandboxCreateMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)

    args = Namespace(uses='jinahub+sandbox://dummy_mwu_encoder')
    host, port = HubIO.deploy_public_sandbox(args)
    assert host == 'http://test_new_deployment.com'
    assert port == 4322
