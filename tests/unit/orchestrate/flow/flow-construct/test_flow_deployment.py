import os

import pytest
from docarray import DocumentArray

from jina import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))
_deployment_yaml_path = os.path.join(cur_dir, '../../../yaml/test-deployment.yml')
_deployment_yaml_with_exec_config_path = os.path.join(
    cur_dir, '../../../yaml/test-deployment-exec-config.yml'
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
