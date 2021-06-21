import os
import time

import pytest

from jina.excepts import RuntimeFailToStart
from jina.executors import BaseExecutor
from jina.parsers import set_pea_parser
from jina.peapods import Pea
from jina.peapods.runtimes.base import BaseRuntime


def bad_func(*args, **kwargs):
    raise Exception('intentional error')


def test_base_pea_with_runtime_bad_init(mocker):
    class Pea1(Pea):
        def __init__(self, args):
            super().__init__(args)
            self.runtime_cls = BaseRuntime

    arg = set_pea_parser().parse_args(['--runtime-backend', 'thread'])
    mocker.patch.object(BaseRuntime, '__init__', bad_func)
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass

    # teardown should be called, cancel should not be called

    teardown_spy.assert_not_called()
    run_spy.assert_not_called()
    cancel_spy.assert_not_called()


def test_base_pea_with_runtime_bad_run_forever(mocker):
    class Pea1(Pea):
        def __init__(self, args):
            super().__init__(args)
            self.runtime_cls = BaseRuntime

    arg = set_pea_parser().parse_args(['--runtime-backend', 'thread'])
    mocker.patch.object(BaseRuntime, 'run_forever', bad_func)
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    with Pea1(arg):
        pass

    # teardown should be called, cancel should not be called

    teardown_spy.assert_called()
    run_spy.assert_called()
    cancel_spy.assert_not_called()


def test_base_pea_with_runtime_bad_teardown(mocker):
    class Pea1(Pea):
        def __init__(self, args):
            super().__init__(args)
            self.runtime_cls = BaseRuntime

    mocker.patch.object(BaseRuntime, 'run_forever', lambda x: time.sleep(3))
    mocker.patch.object(BaseRuntime, 'teardown', lambda x: bad_func)
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

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
            self.runtime_cls = BaseRuntime

    mocker.patch.object(BaseRuntime, 'run_forever', lambda x: time.sleep(3))
    mocker.patch.object(Pea, '_cancel_runtime', bad_func)

    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(Pea, '_cancel_runtime')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    arg = set_pea_parser().parse_args(['--runtime-backend', 'thread'])
    with Pea1(arg):
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
