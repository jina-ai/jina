import json
import multiprocessing
import os
import time

import pytest

from jina.helper import random_port
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from tests.helper import (
    _validate_custom_gateway_process,
    _validate_dummy_custom_gateway_response,
)
from tests.unit.yaml.dummy_gateway import DummyGateway
from tests.unit.yaml.dummy_gateway_get_streamer import DummyGatewayGetStreamer

cur_dir = os.path.dirname(os.path.abspath(__file__))
_dummy_gateway_yaml_path = os.path.join(cur_dir, '../../yaml/test-custom-gateway.yml')
_dummy_fastapi_gateway_yaml_path = os.path.join(
    cur_dir, '../../yaml/test-fastapi-gateway.yml'
)


def _create_gateway_runtime(port, uses, uses_with, worker_port):
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'
    deployments_metadata = '{"pod0": {"key1": "value1", "key2": "value2"}}'
    with GatewayRuntime(
        set_gateway_parser().parse_args(
            [
                '--port',
                str(port),
                '--uses',
                uses,
                '--uses-with',
                json.dumps(uses_with),
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--deployments-metadata',
                deployments_metadata,
            ]
        )
    ) as runtime:
        runtime.run_forever()


def _start_gateway_runtime(uses, uses_with, worker_port):
    port = random_port()

    p = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(port, uses, uses_with, worker_port),
        daemon=True,
    )
    p.start()
    time.sleep(1)
    return port, p


def _create_worker_runtime(port, uses):
    args = set_pod_parser().parse_args(['--uses', uses, '--port', str(port)])

    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _start_worker_runtime(uses):
    port = random_port()

    p = multiprocessing.Process(
        target=_create_worker_runtime,
        args=(port, uses),
        daemon=True,
    )
    p.start()
    time.sleep(1)
    return port, p


@pytest.mark.parametrize(
    'uses,uses_with,expected',
    [
        ('DummyGateway', {}, {'arg1': None, 'arg2': None, 'arg3': 'default-arg3'}),
        (
            'DummyGatewayGetStreamer',
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
            'DummyGateway',
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
            {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
            'DummyGatewayGetStreamer',
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
            'DummyGateway',
            {'arg1': 'arg1'},
            {'arg1': 'arg1', 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
            'DummyGatewayGetStreamer',
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
def test_custom_gateway_no_executors(uses, uses_with, expected):
    worker_port, worker_process = _start_worker_runtime('ProcessExecutor')
    gateway_port, gateway_process = _start_gateway_runtime(uses, uses_with, worker_port)
    _validate_dummy_custom_gateway_response(gateway_port, expected)
    _validate_custom_gateway_process(
        gateway_port, 'hello', {'text': 'helloworld', 'tags': {'processed': True}}
    )
    gateway_process.terminate()
    gateway_process.join()
    worker_process.terminate()
    worker_process.join()

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0
