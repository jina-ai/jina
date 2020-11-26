import os
import subprocess

import pytest

from jina import __version__ as jina_version
from jina.docker.hubio import HubIO
from jina.excepts import PeaFailToStart, HubBuilderError
from jina.executors import BaseExecutor
from jina.flow import Flow
from jina.parser import set_pod_parser, set_hub_build_parser
from jina.peapods import Pod

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_simple_use_abs_import_shall_fail():
    with pytest.raises(ModuleNotFoundError):
        from .dummyhub_abs import DummyHubExecutorAbs
        DummyHubExecutorAbs()

    with pytest.raises(PeaFailToStart):
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
    with Flow().add(uses=f'jinahub/pod.crafter.dummyhubexecutor:0.0.0-{jina_version}'):
        pass


def test_use_executor_pretrained_model_except():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'dummyhub_pretrained'), '--test-uses', '--raise-error'])

    with pytest.raises(HubBuilderError):
        HubIO(args).build()


def test_use_from_cli_level():
    subprocess.check_call(['jina', 'pod', '--uses',
                           os.path.join(cur_dir, 'dummyhub/config.yml'),
                           '--shutdown-idle', '--max-idle-time', '5'])
