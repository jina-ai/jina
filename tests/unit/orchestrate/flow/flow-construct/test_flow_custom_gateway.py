import os

import pytest

from jina import Flow
from tests.helper import (
    ProcessExecutor,
    _validate_custom_gateway_process,
    _validate_dummy_custom_gateway_response,
)
from tests.unit.yaml.dummy_gateway import DummyGateway

cur_dir = os.path.dirname(os.path.abspath(__file__))
_dummy_gateway_yaml_path = os.path.join(
    cur_dir, '../../../yaml/test-custom-gateway.yml'
)


@pytest.mark.parametrize(
    'uses,uses_with,expected',
    [
        ('DummyGateway', {}, {'arg1': None, 'arg2': None, 'arg3': 'default-arg3'}),
        (
            _dummy_gateway_yaml_path,
            {},
            {'arg1': 'hello', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
        (
            'DummyGateway',
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
            _dummy_gateway_yaml_path,
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
            'DummyGateway',
            {'arg1': 'arg1'},
            {'arg1': 'arg1', 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
            _dummy_gateway_yaml_path,
            {'arg1': 'arg1'},
            {'arg1': 'arg1', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
    ],
)
def test_flow_custom_gateway(uses, uses_with, expected):

    flow = (
        Flow()
        .config_gateway(uses=uses, uses_with=uses_with)
        .add(uses='ProcessExecutor')
    )
    with flow:
        _validate_dummy_custom_gateway_response(flow.port, expected)
        _validate_custom_gateway_process(
            flow.port, 'hello', {'text': 'helloworld', 'tags': {'processed': True}}
        )
