import os
from pathlib import Path

import pytest

from jina.hubble import hubapi

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def executor_zip_file():
    return Path(__file__).parent / 'dummy_executor.zip'


@pytest.fixture
def local_hub_executor(test_envs, executor_zip_file):
    hubapi.install_local(executor_zip_file, 'hello', 'v0')


def test_exist_local(test_envs, local_hub_executor):
    assert hubapi.exist_local('hello', 'v0')


def test_resolve_local(test_envs, local_hub_executor):
    assert hubapi.resolve_local('hello', 'v0')


# def test_list_local(test_envs, local_hub_executor):
#     from jina.hubble import hubapi

#     assert len(hubapi.list_local()) == 1


@pytest.mark.parametrize('name', ['dummy_1', 'dummy_2'])
@pytest.mark.parametrize('tag', ['v0', 'v1'])
def test_install_local(test_envs, executor_zip_file, name, tag):
    assert not hubapi.exist_local(name, tag)
    hubapi.install_local(executor_zip_file, name, tag)
    assert hubapi.exist_local(name, tag)

    hubapi.uninstall_local(name)
    assert not hubapi.exist_local(name, tag)


def test_uninstall_locall(test_envs, local_hub_executor):
    hubapi.uninstall_local('hello')
    assert not hubapi.exist_local('hello', None)


def test_load_dump_secret(test_envs):
    import tempfile

    uuid8 = 'hello'
    secret = 'world'
    with tempfile.TemporaryDirectory() as tmpdirname:
        hubapi.dump_secret(Path(tmpdirname), uuid8, secret)
        new_uuid8, new_secret = hubapi.load_secret(Path(tmpdirname))
    assert new_uuid8 == uuid8
    assert new_secret == secret
