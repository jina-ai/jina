import os
from pathlib import Path

import pytest

from jina import __version__ as jina_version
from jina.docker import hubapi
from jina.docker.hubio import HubIO
from jina.excepts import RuntimeFailToStart, HubBuilderError, ImageAlreadyExists
from jina.executors import BaseExecutor
from jina.flow import Flow
from jina.helper import expand_dict
from jina.jaml import JAML
from jina.parsers import set_pod_parser
from jina.parsers.hub import set_hub_build_parser, set_hub_list_parser
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


def test_use_from_local_dir_flow_container_level():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'dummyhub'), '--test-uses', '--raise-error'])
    HubIO(args).build()
    with Flow().add(uses=f'docker://jinahub/pod.crafter.dummyhubexecutor:0.0.0-{jina_version}'):
        pass


def test_use_executor_pretrained_model_except():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'dummyhub_pretrained'), '--test-uses', '--raise-error'])

    with pytest.raises(HubBuilderError):
        HubIO(args).build()


def test_build_timeout_ready():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'dummyhub_slow'), '--timeout-ready', '20000', '--test-uses', '--raise-error'])
    HubIO(args).build()
    with Flow().add(uses=f'docker://jinahub/pod.crafter.dummyhubexecutorslow:0.0.0-{jina_version}',
                    timeout_ready=20000):
        pass


def test_hub_build_push(monkeypatch, mocker):
    mocker.patch.object(HubIO, '_docker_login', return_value=None)
    mocker.patch('jina.docker.hubio._register_to_mongodb', return_value=None)
    args = set_hub_build_parser().parse_args([str(cur_dir + '/hub-mwu'), '--push', '--host-info'])
    mocker.patch('jina.docker.hubio.jina_version', new='0.9.14')
    hubIO = HubIO(args)
    summary = hubIO.build()

    with open(cur_dir + '/hub-mwu' + '/manifest.yml') as fp:
        manifest_jaml = JAML.load(fp, substitute=True)
        manifest = expand_dict(manifest_jaml)

    assert summary['is_build_success']
    assert summary['docker-name']
    assert summary['tag']
    assert summary['jina-version']
    assert manifest['version'] == summary['version']
    # check manifest_info
    assert manifest['description'] == summary['manifest_info']['description']
    assert manifest['author'] == summary['manifest_info']['author']
    assert manifest['kind'] == summary['manifest_info']['kind']
    assert manifest['type'] == summary['manifest_info']['type']
    assert manifest['vendor'] == summary['manifest_info']['vendor']
    assert manifest['keywords'] == summary['manifest_info']['keywords']

    # args = set_hub_list_parser().parse_args([
    #     '--name', summary['manifest_info']['name'],
    #     '--keywords', summary['manifest_info']['keywords'][0],
    #     '--type', summary['manifest_info']['type'],
    # ])
    # response = HubIO(args).list()
    # assert len(response) >= 1


def test_hub_build_push_push_again(mocker):
    mocker.patch.object(HubIO, '_docker_login', return_value=None)
    mocker.patch('jina.docker.hubio._register_to_mongodb', return_value=None)
    args = set_hub_build_parser().parse_args([str(cur_dir) + '/hub-mwu', '--push', '--host-info'])
    mocker.patch('jina.docker.hubio.jina_version', new='0.9.14')
    hubIO = HubIO(args)
    hubIO.build()

    with pytest.raises(ImageAlreadyExists):
        # try and push same version again should fail with `--no-overwrite`
        args = set_hub_build_parser().parse_args([str(cur_dir) + '/hub-mwu', '--push', '--host-info', '--no-overwrite'])
        HubIO(args).build()


def test_hub_build(monkeypatch):
    args = set_hub_build_parser().parse_args([str(cur_dir + '/hub-mwu'), ])
    result = HubIO(args).build()
    assert result['is_build_success']
