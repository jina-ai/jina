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
def local_hub_executor(tmpdir, test_envs):
    from jina.hubble import hubapi, helper, HubExecutor

    hubapi._hub_root = Path(os.environ.get('JINA_HUB_ROOT'))

    pkg_path = Path(__file__).parent / 'dummyhub'
    stream_data = helper.archive_package(pkg_path)
    with open(tmpdir / 'dummy_test.zip', 'wb') as temp_zip_file:
        temp_zip_file.write(stream_data.getvalue())

    hubapi.install_local(
        Path(tmpdir) / 'dummy_test.zip', HubExecutor(uuid='hello', tag='v0')
    )


def test_use_from_local_hub_pod_level(
    test_envs, mocker, monkeypatch, local_hub_executor
):
    from jina.hubble.hubio import HubIO, HubExecutor

    mock = mocker.Mock()

    def _mock_fetch(name, tag=None, secret=None):
        mock(name=name)
        return HubExecutor(
            uuid='hello',
            alias='alias_dummy',
            tag='v0',
            image_name='jinahub/pod.dummy_mwu_encoder',
            md5sum=None,
            visibility=True,
            archive_url=None,
        )

    monkeypatch.setattr(HubIO, '_fetch_meta', _mock_fetch)
    a = set_pod_parser().parse_args(['--uses', 'jinahub://hello'])
    with Pod(a):
        pass


def test_use_from_local_hub_flow_level(
    test_envs, mocker, monkeypatch, local_hub_executor
):
    from jina.hubble.hubio import HubIO, HubExecutor

    mock = mocker.Mock()

    def _mock_fetch(name, tag=None, secret=None):
        mock(name=name)
        return HubExecutor(
            uuid='hello',
            alias='alias_dummy',
            tag='v0',
            image_name='jinahub/pod.dummy_mwu_encoder',
            md5sum=None,
            visibility=True,
            archive_url=None,
        )

    monkeypatch.setattr(HubIO, '_fetch_meta', _mock_fetch)

    with Flow().add(uses='jinahub://hello'):
        pass
