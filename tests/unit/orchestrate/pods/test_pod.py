import os
import time

import pytest

from jina.excepts import RuntimeFailToStart
from jina.orchestrate.pods import Pod
from jina.parsers import set_gateway_parser
from jina.serve.runtimes import asyncio as runtime_asyncio
from jina.serve.executors import BaseExecutor
from tests.helper import _generate_pod_args


@pytest.fixture()
def fake_env():
    os.environ['key_parent'] = 'value3'
    yield
    os.environ.pop('key_parent', None)


class EnvChecker1(BaseExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pod/pod-specific
        assert os.environ['key1'] == 'value1'
        assert os.environ['key2'] == 'value2'
        # inherit from parent process
        assert os.environ['key_parent'] == 'value3'


def test_pod_runtime_env_setting(fake_env):
    args = _generate_pod_args(
        [
            '--uses',
            'EnvChecker1',
            '--env',
            'key1=value1',
            '--env',
            'key2=value2',
        ]
    )
    with Pod(args):
        pass

    # should not affect the main process
    assert 'key1' not in os.environ
    assert 'key2' not in os.environ
    assert 'key_parent' in os.environ


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('grpc', 'GRPCGateway'),
        ('websocket', 'WebSocketGateway'),
        ('http', 'HTTPGateway'),
    ],
)
def test_gateway_args(protocol, expected):
    args = set_gateway_parser().parse_args(
        [
            '--host',
            'jina-custom-gateway',
            '--port',
            '23456',
            '--protocol',
            protocol,
        ]
    )
    p = Pod(args)
    assert p.args.uses == expected


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('grpc', 'GRPCGateway'),
        ('websocket', 'WebSocketGateway'),
        ('http', 'HTTPGateway'),
    ],
)
def test_gateway_runtimes(protocol, expected):
    args = set_gateway_parser().parse_args(
        [
            '--graph-description',
            '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}',
            '--deployments-addresses',
            '{"pod0": ["0.0.0.0:1234"]}',
            '--protocol',
            protocol,
        ]
    )

    with Pod(args) as p:
        assert p.args.uses == expected


class RaisingExecutor(BaseExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise RuntimeError('intentional error')


def test_failing_executor():
    args = _generate_pod_args(
        [
            '--uses',
            'RaisingExecutor',
        ]
    )

    with pytest.raises(RuntimeFailToStart):
        with Pod(args):
            pass


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('grpc', 'GRPCGateway'),
        ('websocket', 'WebSocketGateway'),
        ('http', 'HTTPGateway'),
    ],
)
def test_failing_gateway_runtimes(protocol, expected):
    args = set_gateway_parser().parse_args(
        [
            '--graph-description',
            '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}',
            '--deployments-addresses',
            '{_INVALIDJSONINTENTIONALLY_pod0": ["0.0.0.0:1234"]}',
            '--protocol',
            protocol,
        ]
    )

    with pytest.raises(RuntimeFailToStart):
        with Pod(args):
            pass


@pytest.mark.timeout(4)
def test_close_before_start(monkeypatch):
    class SlowFakeRuntime:
        def __init__(self, *args, **kwargs):
            time.sleep(5.0)

        def __enter__(self):
            pass

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def run_forever(self):
            pass

    monkeypatch.setattr(
        runtime_asyncio,
        'AsyncNewLoopRuntime',
        SlowFakeRuntime,
    )
    pod = Pod(_generate_pod_args(['--noblock-on-start']))
    pod.start()
    pod.close()


@pytest.mark.timeout(4)
def test_close_before_start_slow_enter(monkeypatch):
    class SlowFakeRuntime:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            time.sleep(5.0)

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def run_forever(self):
            pass

    monkeypatch.setattr(
        runtime_asyncio,
        'AsyncNewLoopRuntime',
        SlowFakeRuntime,
    )
    pod = Pod(_generate_pod_args(['--noblock-on-start']))
    pod.start()
    pod.close()
