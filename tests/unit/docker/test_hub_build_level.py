import os

import docker
import pytest
import mock
from mock import Mock, patch

from jina.docker.hubio import HubIO
from jina.enums import BuildTestLevel
from jina.peapods import Pod
from jina.executors import BaseExecutor
from jina.executors import AnyExecutor
from jina.parsers.hub import set_hub_build_parser

@pytest.fixture
def mock_load_config():
    return BaseExecutor

cli = docker.APIClient(base_url='unix://var/run/docker.sock')

def test_hub_build_level_pass(monkeypatch, mock_load_config):

    monkeypatch.setattr(BaseExecutor, "load_config", mock_load_config)
    args = set_hub_build_parser().parse_args(['path/hub-mwu', '--push', '--host-info', '--test-level', 'EXECUTOR'])

    docker_image = cli.get_image('jinahub/pod.dummy_mwu_encoder')
    p_names, failed_levels = HubIO._test_build(docker_image, BuildTestLevel.EXECUTOR, "sample/yaml.yaml", 60, True)
    expected_failed_levels = []
    assert expected_failed_levels == failed_levels


def test_hub_build_level_fail(monkeypatch, mock_load_config):

    monkeypatch.setattr(BaseExecutor, "load_config", mock_load_config)
    args = set_hub_build_parser().parse_args(['path/hub-mwu', '--push', '--host-info', '--test-level', 'FLOW'])

    docker_image = cli.get_image('jinahub/pod.dummy_mwu_encoder')
    expected_failed_levels = [BuildTestLevel.POD_NONDOCKER, BuildTestLevel.POD_DOCKER, BuildTestLevel.FLOW]
    p_names, failed_levels = HubIO(args)._test_build(docker_image, BuildTestLevel.FLOW, 'sampleconfig/yaml', 60, True)
    assert expected_failed_levels == failed_levels