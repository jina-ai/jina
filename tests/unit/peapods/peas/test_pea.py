import os
import time

import pytest
import zmq

from jina.excepts import RuntimeFailToStart, RuntimeRunForeverEarlyError
from jina.executors import BaseExecutor
from jina.parsers import set_gateway_parser, set_pea_parser
from jina.peapods import Pea
from jina.peapods.runtimes.zmq.zed import ZEDRuntime
from jina.types.message.common import ControlMessage


def bad_func(*args, **kwargs):
    raise Exception('intentional error')


def test_base_pea_with_runtime_bad_init(mocker):
    class Pea1(Pea):
        def __init__(self, args):
            super().__init__(args)

    arg = set_pea_parser().parse_args(['--runtime-backend', 'thread'])
    mocker.patch.object(ZEDRuntime, '__init__', bad_func)
    teardown_spy = mocker.spy(ZEDRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(ZEDRuntime, 'run_forever')

    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass

    # teardown should be called, cancel should not be called

    teardown_spy.assert_not_called()
    run_spy.assert_not_called()
    cancel_spy.assert_not_called()


@pytest.mark.slow
def test_base_pea_with_runtime_bad_run_forever(mocker):
    class Pea1(Pea):
        def __init__(self, args):
            super().__init__(args)

    def mock_run_forever(runtime):
        bad_func()

    arg = set_pea_parser().parse_args(['--runtime-backend', 'thread'])
    mocker.patch.object(ZEDRuntime, 'run_forever', mock_run_forever)
    teardown_spy = mocker.spy(ZEDRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(ZEDRuntime, 'run_forever')

    with pytest.raises(RuntimeRunForeverEarlyError):
        with Pea1(arg):
            pass

    # teardown should be called, cancel should not be called
    teardown_spy.assert_called()
    run_spy.assert_called()
    cancel_spy.assert_not_called()


@pytest.mark.slow
def test_base_pea_with_runtime_bad_teardown(mocker):
    class Pea1(Pea):
        def __init__(self, args):
            super().__init__(args)

    def mock_run_forever(*args, **kwargs):
        time.sleep(3)

    def mock_is_ready(*args, **kwargs):
        return True

    def mock_cancel(*args, **kwargs):
        pass

    mocker.patch.object(ZEDRuntime, 'run_forever', mock_run_forever)
    mocker.patch.object(ZEDRuntime, 'is_ready', mock_is_ready)
    mocker.patch.object(ZEDRuntime, 'teardown', lambda x: bad_func)
    mocker.patch.object(ZEDRuntime, 'cancel', lambda *args, **kwargs: mock_cancel)
    teardown_spy = mocker.spy(ZEDRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(ZEDRuntime, 'run_forever')

    arg = set_pea_parser().parse_args(['--runtime-backend', 'thread'])
    with Pea1(arg):
        pass

    teardown_spy.assert_called()
    run_spy.assert_called()
    cancel_spy.assert_called_once()  # 3s > .join(1), need to cancel

    # run_forever cancel should all be called


def test_base_pea_with_runtime_bad_cancel(mocker):
    class Pea1(Pea):
        def __init__(self, args):
            super().__init__(args)

    def mock_run_forever(runtime):
        time.sleep(3)

    def mock_is_ready(*args, **kwargs):
        return True

    mocker.patch.object(ZEDRuntime, 'run_forever', mock_run_forever)
    mocker.patch.object(ZEDRuntime, 'is_ready', mock_is_ready)
    mocker.patch.object(Pea, '_cancel_runtime', bad_func)

    teardown_spy = mocker.spy(ZEDRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(ZEDRuntime, 'run_forever')

    arg = set_pea_parser().parse_args(['--runtime-backend', 'thread'])
    with Pea1(arg):
        time.sleep(0.1)
        pass

    teardown_spy.assert_called()
    run_spy.assert_called()
    cancel_spy.assert_called_once()

    # run_forever cancel should all be called


@pytest.fixture()
def fake_env():
    os.environ['key_parent'] = 'value3'
    yield
    os.unsetenv('key_parent')


def test_pea_runtime_env_setting_in_process(fake_env):
    class EnvChecker(BaseExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # pea/pod-specific
            assert os.environ['key1'] == 'value1'
            assert os.environ['key2'] == 'value2'
            # inherit from parent process
            assert os.environ['key_parent'] == 'value3'

    with Pea(
        set_pea_parser().parse_args(
            [
                '--uses',
                'EnvChecker',
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


def test_pea_runtime_env_setting_in_thread(fake_env):
    class EnvChecker(BaseExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # pea/pod-specific
            assert 'key1' not in os.environ
            assert 'key2' not in os.environ
            # inherit from parent process
            assert os.environ['key_parent'] == 'value3'

    os.environ['key_parent'] = 'value3'

    with Pea(
        set_pea_parser().parse_args(
            [
                '--uses',
                'EnvChecker',
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

    os.unsetenv('key_parent')


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('grpc', 'GRPCRuntime'),
        ('websocket', 'WebSocketRuntime'),
        ('http', 'HTTPRuntime'),
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


@pytest.mark.timeout(30)
@pytest.mark.slow
@pytest.mark.parametrize(
    'command, response_expected',
    [
        ('IDLE', 0),
        ('CANCEL', 0),
        ('TERMINATE', 1),
        ('STATUS', 1),
        ('ACTIVATE', 1),
        ('DEACTIVATE', 1),
    ],
)
def test_idle_does_not_create_response(command, response_expected):
    args = set_pea_parser().parse_args([])

    with Pea(args) as p:
        msg = ControlMessage(command, pod_name='fake_pod')

        with zmq.Context().socket(zmq.PAIR) as socket:
            socket.connect(f'tcp://localhost:{p.args.port_ctrl}')
            socket.send_multipart(msg.dump())
            assert socket.poll(timeout=1000) == response_expected
