import os
import time

import pytest

from jina.excepts import RuntimeFailToStart
from jina.executors import BaseExecutor
from jina.parsers import set_gateway_parser, set_pea_parser
from jina.peapods import Pea, runtimes


@pytest.fixture()
def fake_env():
    os.environ['key_parent'] = 'value3'
    yield
    os.environ.pop('key_parent', None)


class EnvChecker1(BaseExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pea/pod-specific
        assert os.environ['key1'] == 'value1'
        assert os.environ['key2'] == 'value2'
        # inherit from parent process
        assert os.environ['key_parent'] == 'value3'


def test_pea_runtime_env_setting_in_process(fake_env):
    with Pea(
        set_pea_parser().parse_args(
            [
                '--uses',
                'EnvChecker1',
                '--env',
                'key1=value1',
                '--env',
                'key2=value2',
                '--runtime-backend',
                'process',
            ]
        )
    ):
        pass

    # should not affect the main process
    assert 'key1' not in os.environ
    assert 'key2' not in os.environ
    assert 'key_parent' in os.environ


class EnvChecker2(BaseExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pea/pod-specific
        assert 'key1' not in os.environ
        assert 'key2' not in os.environ
        # inherit from parent process
        assert os.environ['key_parent'] == 'value3'


@pytest.mark.skip('grpc in threads messes up and produces handing servers')
def test_pea_runtime_env_setting_in_thread(fake_env):
    os.environ['key_parent'] = 'value3'

    with Pea(
        set_pea_parser().parse_args(
            [
                '--uses',
                'EnvChecker2',
                '--env',
                'key1=value1',
                '--env',
                'key2=value2',
                '--runtime-backend',
                'thread',
            ]
        )
    ):
        pass

    # should not affect the main process
    assert 'key1' not in os.environ
    assert 'key2' not in os.environ
    assert 'key_parent' in os.environ
    os.environ.pop('key_parent')


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('grpc', 'GRPCGatewayRuntime'),
        ('websocket', 'WebSocketGatewayRuntime'),
        ('http', 'HTTPGatewayRuntime'),
    ],
)
def test_gateway_args(protocol, expected):
    args = set_gateway_parser().parse_args(
        [
            '--host',
            'jina-custom-gateway',
            '--port-expose',
            '23456',
            '--protocol',
            protocol,
        ]
    )
    p = Pea(args)
    assert p.runtime_cls.__name__ == expected


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('grpc', 'GRPCGatewayRuntime'),
        ('websocket', 'WebSocketGatewayRuntime'),
        ('http', 'HTTPGatewayRuntime'),
    ],
)
def test_gateway_runtimes(protocol, expected):
    args = set_gateway_parser().parse_args(
        [
            '--graph-description',
            '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}',
            '--pods-addresses',
            '{"pod0": ["0.0.0.0:1234"]}',
            '--protocol',
            protocol,
        ]
    )

    with Pea(args) as p:
        assert p.runtime_cls.__name__ == expected


@pytest.mark.parametrize(
    'runtime_cls',
    ['WorkerRuntime', 'HeadRuntime'],
)
def test_non_gateway_runtimes(runtime_cls):
    args = set_pea_parser().parse_args(
        [
            '--runtime-cls',
            runtime_cls,
        ]
    )

    with Pea(args) as p:
        assert p.runtime_cls.__name__ == runtime_cls


class RaisingExecutor(BaseExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise RuntimeError('intentional error')


def test_failing_executor():
    args = set_pea_parser().parse_args(
        [
            '--uses',
            'RaisingExecutor',
        ]
    )

    with pytest.raises(RuntimeFailToStart):
        with Pea(args):
            pass


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('grpc', 'GRPCGatewayRuntime'),
        ('websocket', 'WebSocketGatewayRuntime'),
        ('http', 'HTTPGatewayRuntime'),
    ],
)
def test_failing_gateway_runtimes(protocol, expected):
    args = set_gateway_parser().parse_args(
        [
            '--graph-description',
            '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}',
            '--pods-addresses',
            '{_INVALIDJSONINTENTIONALLY_pod0": ["0.0.0.0:1234"]}',
            '--protocol',
            protocol,
        ]
    )

    with pytest.raises(RuntimeFailToStart):
        with Pea(args):
            pass


def test_failing_head():
    args = set_pea_parser().parse_args(
        [
            '--runtime-cls',
            'HeadRuntime',
        ]
    )
    args.port_in = None

    with pytest.raises(RuntimeFailToStart):
        with Pea(args):
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
        runtimes,
        'get_runtime',
        lambda *args, **kwargs: SlowFakeRuntime,
    )
    pea = Pea(set_pea_parser().parse_args(['--noblock-on-start']))
    pea.start()
    pea.close()


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
        runtimes,
        'get_runtime',
        lambda *args, **kwargs: SlowFakeRuntime,
    )
    pea = Pea(set_pea_parser().parse_args(['--noblock-on-start']))
    pea.start()
    pea.close()
