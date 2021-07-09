import os
import json
from pathlib import Path
import requests
import pytest

from jina import Flow
from jina.excepts import RuntimeFailToStart
from jina.executors import BaseExecutor
from jina.parsers import set_pod_parser
from jina.peapods import Pod

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_simple_use_abs_import_shall_fail():
    with pytest.raises(ModuleNotFoundError):
        from .dummyhub_abs import DummyHubExecutorAbs

        DummyHubExecutorAbs()

    with pytest.raises(RuntimeFailToStart):
        with Flow().add(uses='DummyHubExecutorAbs'):
            pass


def test_simple_use_relative_import():
    from .dummyhub import DummyHubExecutor

    DummyHubExecutor()

    with Flow().add(uses='DummyHubExecutor'):
        pass


def test_use_from_local_dir_exe_level():
    with BaseExecutor.load_config('dummyhub/config.yml'):
        pass


def test_use_from_local_dir_pod_level():
    a = set_pod_parser().parse_args(['--uses', 'dummyhub/config.yml'])
    with Pod(a):
        pass


def test_use_from_local_dir_flow_level():
    with Flow().add(uses='dummyhub/config.yml'):
        pass


@pytest.fixture
def local_hub_executor(mocker, monkeypatch, tmpdir, test_envs):
    class GetMockResponse:
        def __init__(self, response_code: int = 201):
            self.response_code = response_code

        def json(self):
            return {
                'keywords': [],
                'id': 'hello',
                'alias': 'alias_name',
                'tag': 'v0',
                'versions': [],
                'visibility': 'public',
                'image': 'jinahub/hello:v0',
                'package': {
                    'download': 'http://hubbleapi.jina.ai/files/helloworld_v0.zip',
                    'md5': 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f',
                },
            }

        @property
        def text(self):
            return json.dumps(self.json())

        @property
        def status_code(self):
            return self.response_code

    mock = mocker.Mock()

    def _mock_get(url, headers=None):
        mock(url=url)
        return GetMockResponse(response_code=requests.codes.ok)

    monkeypatch.setattr(requests, 'get', _mock_get)

    from jina.hubble import hubapi, helper, HubExecutor

    pkg_path = Path(__file__).parent / 'dummyhub'
    stream_data = helper.archive_package(pkg_path)
    with open(tmpdir / 'dummy_test.zip', 'wb') as temp_zip_file:
        temp_zip_file.write(stream_data.getvalue())
    hubapi.install_local(
        Path(tmpdir) / 'dummy_test.zip', HubExecutor(uuid='hello', tag='v0')
    )


def test_use_from_local_hub_pod_level(local_hub_executor):
    a = set_pod_parser().parse_args(['--uses', 'jinahub://hello'])
    with Pod(a):
        pass


def test_use_from_local_hub_flow_level(local_hub_executor):
    with Flow().add(uses='jinahub://hello'):
        pass
