import os
from pathlib import Path

import pytest
from jina.logging.logger import JinaLogger

from jina import __version__ as jina_version
from jina.excepts import RuntimeFailToStart, HubBuilderError, ImageAlreadyExists
from jina.executors import BaseExecutor
from jina import Flow
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
