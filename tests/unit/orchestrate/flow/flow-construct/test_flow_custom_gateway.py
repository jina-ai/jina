import os

import pytest
import requests

from jina import Flow
from tests.helper import (
    ProcessExecutor,
    _validate_custom_gateway_process,
    _validate_dummy_custom_gateway_response,
)
from tests.unit.yaml.dummy_gateway import DummyGateway
from tests.unit.yaml.dummy_gateway_get_streamer import DummyGatewayGetStreamer

cur_dir = os.path.dirname(os.path.abspath(__file__))
_dummy_gateway_yaml_path = os.path.join(
    cur_dir, '../../../yaml/test-custom-gateway.yml'
)

_dummy_fastapi_gateway_yaml_path = os.path.join(
    cur_dir, '../../../yaml/test-fastapi-gateway.yml'
)

_flow_with_dummy_gateway_yaml_path = os.path.join(
    cur_dir, '../../../yaml/test-flow-custom-gateway-nested-config.yml'
)


@pytest.mark.parametrize(
    'uses,uses_with,expected',
    [
        (DummyGateway, {}, {'arg1': None, 'arg2': None, 'arg3': 'default-arg3'}),
        (
            DummyGatewayGetStreamer,
            {},
            {'arg1': None, 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
            _dummy_gateway_yaml_path,
            {},
            {'arg1': 'hello', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
        (
            _dummy_fastapi_gateway_yaml_path,
            {},
            {'arg1': 'hello', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
        (
            DummyGateway,
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
            DummyGatewayGetStreamer,
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
            _dummy_gateway_yaml_path,
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
            _dummy_fastapi_gateway_yaml_path,
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
            DummyGateway,
            {'arg1': 'arg1'},
            {'arg1': 'arg1', 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
            DummyGatewayGetStreamer,
            {'arg1': 'arg1'},
            {'arg1': 'arg1', 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
            _dummy_gateway_yaml_path,
            {'arg1': 'arg1'},
            {'arg1': 'arg1', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
        (
            _dummy_fastapi_gateway_yaml_path,
            {'arg1': 'arg1'},
            {'arg1': 'arg1', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
    ],
)
def test_flow_custom_gateway_no_executor(uses, uses_with, expected):

    flow = (
        Flow().config_gateway(uses=uses, uses_with=uses_with).add(uses=ProcessExecutor)
    )
    with flow:
        _validate_dummy_custom_gateway_response(flow.port, expected)
        _validate_custom_gateway_process(
            flow.port, 'hello', {'text': 'helloworld', 'tags': {'processed': True}}
        )


def test_flow_fastapi_default_health_check():

    flow = (
        Flow()
        .config_gateway(
            uses=_dummy_fastapi_gateway_yaml_path,
            uses_with={'default_health_check': True},
        )
        .add(uses='ProcessExecutor')
    )
    with flow:
        _validate_dummy_custom_gateway_response(flow.port, {})
        _validate_custom_gateway_process(
            flow.port, 'hello', {'text': 'helloworld', 'tags': {'processed': True}}
        )


def test_flow_custom_gateway_nested_config():

    flow = Flow.load_config(_flow_with_dummy_gateway_yaml_path)
    with flow:
        _validate_dummy_custom_gateway_response(
            flow.port, {'arg1': 'hello', 'arg2': 'world', 'arg3': 'default-arg3'}
        )


def test_flow_custom_gateway_via_flow_uses_disabled():
    uses_with = {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'}
    flow = Flow(uses='DummyGateway', uses_with=uses_with)

    # the uses parameter is ignored here and not be applied on the gateway, therefore, the gateway
    # is just a GRPC gateway
    with pytest.raises(requests.ConnectionError):
        with flow:
            _ = requests.get(f'http://127.0.0.1:{flow.port}/').json()
