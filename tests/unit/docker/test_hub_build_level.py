import pytest

from jina.docker.hubio import HubIO
from jina.enums import BuildTestLevel
from jina.executors import BaseExecutor
from jina.parser import set_hub_build_parser


@pytest.fixture
def mock_load_config():
    return BaseExecutor


def test_hub_build_level_pass(monkeypatch, mock_load_config):
    monkeypatch.setattr(BaseExecutor, "load_config", mock_load_config)
    args = set_hub_build_parser().parse_args(['path/hub-mwu', '--push', '--host-info', '--test-level', 'EXECUTOR'])

    p_names, failed_levels = HubIO._test_build("jinahub/pod.dummy_mwu_encoder", BuildTestLevel.EXECUTOR,
                                               "sample/yaml.yaml", True)
    expected_failed_levels = []
    assert expected_failed_levels == failed_levels


def test_hub_build_level_fail(monkeypatch, mock_load_config):
    monkeypatch.setattr(BaseExecutor, "load_config", mock_load_config)
    args = set_hub_build_parser().parse_args(['path/hub-mwu', '--push', '--host-info', '--test-level', 'FLOW'])

    expected_failed_levels = [BuildTestLevel.POD_NONDOCKER, BuildTestLevel.POD_DOCKER, BuildTestLevel.FLOW]
    p_names, failed_levels = HubIO(args)._test_build("jinahub/pod.dummy_mwu_encoder", BuildTestLevel.FLOW,
                                                     'sampleconfig/yaml', True)
    assert expected_failed_levels == failed_levels
