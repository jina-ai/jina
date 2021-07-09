import os
from pathlib import Path

import pytest

from jina.hubble import hubapi, HubExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def executor_zip_file():
    return Path(__file__).parent / 'dummy_executor.zip'


@pytest.fixture
def test_executor():
    return HubExecutor(uuid='hello', alias=None, sn=0, tag='v0')


# @pytest.fixture
# def local_hub_executor(test_envs, executor_zip_file, test_executor):
#     hubapi.install_local(executor_zip_file, test_executor)


# def test_exist_local(test_envs, local_hub_executor):
#     assert hubapi.exist_local('hello', 'v0')


# def test_resolve_local(test_envs, local_hub_executor, test_executor):
#     pkg, pkg_dist = hubapi.resolve_local(test_executor)
#     assert pkg is not None
#     assert pkg_dist is not None


def test_install_local(test_envs, executor_zip_file, test_executor):
    assert not hubapi.exist_local(test_executor.uuid, test_executor.tag)
    hubapi.install_local(executor_zip_file, test_executor)
    assert hubapi.exist_local(test_executor.uuid, test_executor.tag)

    hubapi.uninstall_local(test_executor.uuid)
    assert not hubapi.exist_local(test_executor.uuid, test_executor.tag)


# def test_uninstall_locall(test_envs, local_hub_executor):
#     hubapi.uninstall_local('hello')
#     assert not hubapi.exist_local('hello', None)


def test_load_dump_secret(test_envs):
    import tempfile

    uuid8 = 'hello'
    secret = 'world'
    with tempfile.TemporaryDirectory() as tmpdirname:
        hubapi.dump_secret(Path(tmpdirname), uuid8, secret)
        new_uuid8, new_secret = hubapi.load_secret(Path(tmpdirname))
    assert new_uuid8 == uuid8
    assert new_secret == secret
