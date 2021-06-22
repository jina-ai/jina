import os
import json
import pytest
import requests
from pathlib import Path


cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def executor_zip_file():
    return Path(__file__).parent / 'dummy_executor.zip'


@pytest.fixture
def local_hub_executor(executor_zip_file, test_envs):
    from jina.hubble import hubapi

    hubapi.install_locall(executor_zip_file, 'hello', 'v0')


def test_exist_locall(local_hub_executor):
    from jina.hubble import hubapi

    assert hubapi.exist_locall('hello', 'v0')


def test_resolve_local(local_hub_executor):
    from jina.hubble import hubapi, JINA_HUB_ROOT

    assert hubapi.resolve_local('hello', 'v0') == JINA_HUB_ROOT / 'hello'


def test_list_local(local_hub_executor):
    from jina.hubble import hubapi

    assert len(hubapi.list_local()) == 1


@pytest.mark.parametrize('name', ['dummy_1', 'dummy_2'])
@pytest.mark.parametrize('tag', ['v0', 'v1'])
def test_install_locall(test_envs, executor_zip_file, name, tag):
    from jina.hubble import hubapi

    assert not hubapi.exist_locall(name, tag)
    hubapi.install_locall(executor_zip_file, name, tag)
    assert hubapi.exist_locall(name, tag)

    hubapi.uninstall_locall(name)
    assert not hubapi.exist_locall(name, tag)


def test_uninstall_locall(test_envs, local_hub_executor):
    from jina.hubble import hubapi

    hubapi.uninstall_locall('hello')
    assert not hubapi.exist_locall('hello', None)
