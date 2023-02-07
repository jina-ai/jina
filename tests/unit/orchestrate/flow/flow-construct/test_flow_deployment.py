import os

import pytest
from docarray import DocumentArray

from jina import Deployment, Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))
_deployment_yaml_path = os.path.join(cur_dir, '../../../yaml/test-deployment.yml')
_deployment_yaml_with_exec_config_path = os.path.join(
    cur_dir, '../../../yaml/test-deployment-exec-config.yml'
)
_flow_yaml_with_deployment_config = os.path.join(
    cur_dir, '../../../yaml/test-flow-deployment-nested-config.yml'
)
_flow_yaml_with_deployment_config_deployments_keyword = os.path.join(
    cur_dir, '../../../yaml/test-flow-deployment-nested-config-deployments-keyword.yml'
)
_flow_yaml_with_deployment_exec_config = os.path.join(
    cur_dir, '../../../yaml/test-flow-deployment-exec-nested-config.yml'
)
_flow_yaml_with_embedded_deployment_config = os.path.join(
    cur_dir, '../../../yaml/test-flow-deployment-embedded-config.yml'
)
_flow_yaml_with_embedded_deployment_config_deployments_keyword = os.path.join(
    cur_dir,
    '../../../yaml/test-flow-deployment-embedded-config-deployments-keyword.yml',
)


@pytest.mark.parametrize(
    'deployment_config',
    [_deployment_yaml_path, _deployment_yaml_with_exec_config_path],
)
def test_flow_deployment(deployment_config):

    flow = Flow().add(deployment=deployment_config)
    with flow:
        docs = flow.post(on='/', inputs=DocumentArray.empty(3))
        assert len(docs) == 3
        assert all([doc.text == 'indexed' for doc in docs])


@pytest.mark.parametrize(
    'flow_config',
    [
        _flow_yaml_with_deployment_config,
        _flow_yaml_with_deployment_exec_config,
        _flow_yaml_with_deployment_config_deployments_keyword,
        _flow_yaml_with_embedded_deployment_config,
        _flow_yaml_with_embedded_deployment_config_deployments_keyword,
    ],
)
def test_flow_load_config_with_deployment(flow_config):

    flow = Flow.load_config(flow_config)
    with flow:
        docs = flow.post(on='/', inputs=DocumentArray.empty(3))
        assert len(docs) == 3
        assert all([doc.text == 'indexed' for doc in docs])
