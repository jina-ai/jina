import os
import json
import pytest

import tempfile
from pathlib import Path


cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def executor_zip_file():
    return Path(__file__).parent / 'dummy_executor.zip'


@pytest.mark.parametrize('name', ['dummy_1', 'dummy_2'])
@pytest.mark.parametrize('tag', ['v0', 'v1'])
def test_install_local(tmpdir, test_envs, executor_zip_file, name, tag):
    from jina.hubble import hubapi

    assert not hubapi.exist_locall(name, tag)
    hubapi.install_locall(executor_zip_file, name, tag)
    assert hubapi.exist_locall(name, tag)

    hubapi.uninstall_locall(name)
    assert not hubapi.exist_locall(name, tag)
