import os
from pathlib import Path

import docker
import pytest
from jina.logging import JinaLogger

from jina.enums import BuildTestLevel

from jina import __version__ as jina_version
from jina.docker import hubapi
from jina.docker.hubio import HubIO
from jina.excepts import RuntimeFailToStart, HubBuilderError, ImageAlreadyExists
from jina.executors import BaseExecutor
from jina.flow import Flow
from jina.helper import expand_dict
from jina.jaml import JAML
from jina.parsers import set_pod_parser
from jina.parsers.hub import (
    set_hub_build_parser,
    set_hub_list_parser,
    set_hub_pushpull_parser,
    set_hub_new_parser,
)
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
        [os.path.join(cur_dir, 'dummyhub'), '--test-uses', '--raise-error']
    )
    HubIO(args).build()
    with Flow().add(
        uses=f'docker://jinahub/pod.crafter.dummyhubexecutor:0.0.0-{jina_version}'
    ):
        pass


def test_use_executor_pretrained_model_except():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'dummyhub_pretrained'), '--test-uses', '--raise-error']
    )

    with pytest.raises(HubBuilderError):
        HubIO(args).build()


def test_build_timeout_ready():
    args = set_hub_build_parser().parse_args(
        [
            os.path.join(cur_dir, 'dummyhub_slow'),
            '--timeout-ready',
            '20000',
            '--test-uses',
            '--raise-error',
        ]
    )
    HubIO(args).build()
    with Flow().add(
        uses=f'docker://jinahub/pod.crafter.dummyhubexecutorslow:0.0.0-{jina_version}',
        timeout_ready=20000,
    ):
        pass


@pytest.mark.timeout(360)
def test_hub_pull():
    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder:0.0.6'])
    HubIO(args).pull()


@pytest.mark.timeout(360)
def test_hub_list():
    args = set_hub_list_parser().parse_args(['--keywords', 'numeric'])
    response = HubIO(args).list()
    assert len(response) > 0


@pytest.mark.timeout(360)
def test_hub_list_non_existing_kind():
    args = set_hub_list_parser().parse_args(['--kind', 'does-not-exist'])
    response = HubIO(args).list()
    assert not response


@pytest.mark.skip('https://github.com/jina-ai/jina/issues/1641')
@pytest.mark.skipif(
    condition='GITHUB_TOKEN' not in os.environ, reason='Token not found'
)
def test_hub_build_push(monkeypatch, mocker):
    monkeypatch.setattr(Path, 'is_file', True)
    mock_access_token = mocker.patch.object(
        hubapi, '_fetch_access_token', autospec=True
    )
    mock_access_token.return_value = os.environ.get('GITHUB_TOKEN', None)
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--push', '--host-info']
    )
    summary = HubIO(args).build()

    with open(cur_dir + '/hub-mwu' + '/manifest.yml') as fp:
        manifest_jaml = JAML.load(fp, substitute=True)
        manifest = expand_dict(manifest_jaml)

    assert summary['is_build_success']
    assert manifest['version'] == summary['version']
    assert manifest['description'] == summary['manifest_info']['description']
    assert manifest['author'] == summary['manifest_info']['author']
    assert manifest['kind'] == summary['manifest_info']['kind']
    assert manifest['type'] == summary['manifest_info']['type']
    assert manifest['vendor'] == summary['manifest_info']['vendor']
    assert manifest['keywords'] == summary['manifest_info']['keywords']

    args = set_hub_list_parser().parse_args(
        [
            '--name',
            summary['manifest_info']['name'],
            '--keywords',
            summary['manifest_info']['keywords'][0],
            '--type',
            summary['manifest_info']['type'],
        ]
    )
    response = HubIO(args).list()
    manifests = response

    assert len(manifests) >= 1
    assert manifests[0]['name'] == summary['manifest_info']['name']


@pytest.mark.skip('https://github.com/jina-ai/jina/issues/1641')
@pytest.mark.skipif(
    condition='GITHUB_TOKEN' not in os.environ, reason='Token not found'
)
def test_hub_build_push_push_again(monkeypatch, mocker):
    monkeypatch.setattr(Path, 'is_file', True)
    mock_access_token = mocker.patch.object(
        hubapi, '_fetch_access_token', autospec=True
    )
    mock_access_token.return_value = os.environ.get('GITHUB_TOKEN', None)

    args = set_hub_build_parser().parse_args(
        [str(cur_dir) + '/hub-mwu', '--push', '--host-info']
    )
    summary = HubIO(args).build()

    with open(str(cur_dir) + '/hub-mwu' + '/manifest.yml') as fp:
        manifest_jaml = JAML.load(fp, substitute=True)
        manifest = expand_dict(manifest_jaml)

    assert summary['is_build_success']
    assert manifest['version'] == summary['version']
    assert manifest['description'] == summary['manifest_info']['description']
    assert manifest['author'] == summary['manifest_info']['author']
    assert manifest['kind'] == summary['manifest_info']['kind']
    assert manifest['type'] == summary['manifest_info']['type']
    assert manifest['vendor'] == summary['manifest_info']['vendor']
    assert manifest['keywords'] == summary['manifest_info']['keywords']

    args = set_hub_list_parser().parse_args(
        [
            '--name',
            summary['manifest_info']['name'],
            '--keywords',
            summary['manifest_info']['keywords'][0],
            '--type',
            summary['manifest_info']['type'],
        ]
    )
    response = HubIO(args).list()
    manifests = response

    assert len(manifests) >= 1
    assert manifests[0]['name'] == summary['manifest_info']['name']

    with pytest.raises(ImageAlreadyExists):
        # try and push same version again should fail with `--no-overwrite`
        args = set_hub_build_parser().parse_args(
            [str(cur_dir) + '/hub-mwu', '--push', '--host-info', '--no-overwrite']
        )
        HubIO(args).build()


@pytest.mark.timeout(360)
@pytest.mark.parametrize(
    'dockerfile_path',
    [
        os.path.join(cur_dir, 'hub-mwu'),
        os.path.relpath(os.path.join(cur_dir, 'hub-mwu'), os.getcwd()),
    ],
)
def test_hub_build_multistage(dockerfile_path):
    args = set_hub_build_parser().parse_args(
        [dockerfile_path, '--raise-error', '-f', 'multistage.Dockerfile']
    )
    result = HubIO(args).build()
    assert result['is_build_success']


@pytest.mark.parametrize('new_type', ['pod', 'app', 'template'])
def test_create_new(tmpdir, new_type):
    args = set_hub_new_parser().parse_args(
        ['--output-dir', str(tmpdir), '--type', new_type]
    )
    HubIO(args).new(no_input=True)
    list_dir = os.listdir(str(tmpdir))
    assert len(list_dir) == 1


@pytest.fixture(scope='function')
def test_workspace(tmpdir):
    os.environ['JINA_TEST_JOINT'] = str(tmpdir)
    workspace_path = os.environ['JINA_TEST_JOINT']
    yield workspace_path
    del os.environ['JINA_TEST_JOINT']


@pytest.fixture(scope='function')
def docker_image():
    def _filter_repo_tag(image, image_name='jinahub/pod.dummy_mwu_encoder'):
        tags = image.attrs['RepoTags'] if 'RepoTags' in image.attrs else None
        if tags:
            return tags[0].startswith(image_name)
        else:
            return False

    img_name = 'jinahub/pod.dummy_mwu_encoder:0.0.6'
    client = docker.from_env()
    client.images.pull(img_name)
    images = client.images.list()
    image_name = list(filter(lambda image: _filter_repo_tag(image), images))[0]
    return image_name


def test_hub_build_level_pass(monkeypatch, test_workspace, docker_image):
    args = set_hub_build_parser().parse_args(
        ['path/hub-mwu', '--push', '--host-info', '--test-level', 'EXECUTOR']
    )
    expected_failed_levels = []

    _, failed_levels = HubIO(args)._test_build(
        docker_image,
        BuildTestLevel.EXECUTOR,
        os.path.join(cur_dir, 'yaml/test-executor.yml'),
        60000,
        True,
        JinaLogger('unittest'),
    )

    assert expected_failed_levels == failed_levels


def test_hub_build_level_fail(monkeypatch, test_workspace, docker_image):
    args = set_hub_build_parser().parse_args(
        ['path/hub-mwu', '--push', '--host-info', '--test-level', 'FLOW']
    )
    expected_failed_levels = [BuildTestLevel.POD_DOCKER, BuildTestLevel.FLOW]

    _, failed_levels = HubIO(args)._test_build(
        docker_image,
        BuildTestLevel.FLOW,
        os.path.join(cur_dir, 'yaml/test-executor.yml'),
        60000,
        True,
        JinaLogger('unittest'),
    )

    assert expected_failed_levels == failed_levels
