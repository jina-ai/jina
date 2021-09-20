import argparse
import os
import json
import urllib
import shutil
import docker
import pytest
import requests
import itertools
from pathlib import Path

from jina.hubble.helper import disk_cache_offline
from jina.hubble.hubio import HubIO, HubExecutor
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

    def iter_lines(self):
        logs = [
            '{"stream":"Receiving zip file..."}',
            '{"stream":"Normalizing the content..."}',
            '{"stream":"Building the image..."}',
            '{"stream":"Uploading the image..."}',
            '{"stream":"Uploading the zip..."}',
            '{"result":{"statusCode":201,"message":"Successfully pushed w7qckiqy","data":{"executors":[{"tag":"v0","id":"w7qckiqy","image":"jinahub/w7qckiqy:v0","pullPath":"jinahub/w7qckiqy:v0","secret":"a26531e561dcb7af2c999a64cadc86d0","visibility":"public"}]}}}',
        ]

        return itertools.chain(logs)


class GetMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def json(self):
        return {
            'keywords': [],
            'id': 'dummy_mwu_encoder',
            'name': 'alias_dummy',
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

    def _mock_get(url, headers=None):
        mock(url=url)
        return GetMockResponse(response_code=200)

    monkeypatch.setattr(requests, 'get', _mock_get)
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    executor = HubIO(args).fetch_meta('dummy_mwu_encoder')

    assert executor.uuid == 'dummy_mwu_encoder'
    assert executor.name == 'alias_dummy'
    assert executor.tag == 'v0'
    assert executor.image_name == 'jinahub/pod.dummy_mwu_encoder'
    assert executor.md5sum == 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f'


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

    def _mock_fetch(name, tag=None, secret=None, force=False):
        mock(name=name)
        return HubExecutor(
            uuid='dummy_mwu_encoder',
            name='alias_dummy',
            tag='v0',
            image_name='jinahub/pod.dummy_mwu_encoder',
            md5sum=None,
            visibility=True,
            archive_url=None,
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
    def _mock_fetch(name, tag=None, secret=None, force=False):
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
        HubIO,
        '_load_docker_client',
        _gen_load_docker_client(fail_pull=True),
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
        HubIO,
        '_load_docker_client',
        _gen_load_docker_client(fail_pull=False),
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v0'

    version = 'v1'
    # expect successful forced pull because force == True
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'

    # expect successful pull using cached fetch_meta response and saved image
    fail_meta_fetch = True
    monkeypatch.setattr(
        HubIO,
        '_load_docker_client',
        _gen_load_docker_client(fail_pull=False),
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'

    args.force = False
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
def test_new(monkeypatch, tmpdir, add_dockerfile):
    from rich.prompt import Prompt, Confirm

    prompts = iter(
        [
            'DummyExecutor',
            tmpdir / 'DummyExecutor',
            'dummy description',
            'dummy author',
            'dummy tags',
            'dummy docs',
        ]
    )

    confirms = iter([True, add_dockerfile])

    def _mock_prompt_ask(*args, **kwargs):
        return next(prompts)

    def _mock_confirm_ask(*args, **kwargs):
        return next(confirms)

    monkeypatch.setattr(Prompt, 'ask', _mock_prompt_ask)
    monkeypatch.setattr(Confirm, 'ask', _mock_confirm_ask)

    args = argparse.Namespace(hub='new')
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
