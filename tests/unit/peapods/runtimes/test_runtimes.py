import time

import pytest

from jina.excepts import RuntimeFailToStart
from jina.parsers import set_pea_parser, set_gateway_parser
from jina.peapods.peas.base import BasePea
from jina.peapods.runtimes.asyncio.grpc import GRPCRuntime
from jina.peapods.runtimes.asyncio.rest import RESTRuntime
from jina.peapods.runtimes.base import BaseRuntime
from jina.peapods.runtimes.container import ContainerRuntime
from jina.peapods.runtimes.zmq.zed import ZEDRuntime


def bad_func(*args, **kwargs):
    raise Exception('intentional error')


def test_base_runtime_bad_init(mocker):
    class Pea1(BasePea):
        runtime_cls = BaseRuntime

    arg = set_pea_parser().parse_args(['--runtime', 'thread'])
    mocker.patch.object(BaseRuntime, '__init__', bad_func)
    setup_spy = mocker.spy(BaseRuntime, 'setup')
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(BaseRuntime, 'cancel')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass

    # teardown, setup should be called, cancel should not be called

    setup_spy.assert_not_called()
    teardown_spy.assert_not_called()
    run_spy.assert_not_called()
    cancel_spy.assert_not_called()


def test_base_runtime_bad_run_forever(mocker):
    class Pea1(BasePea):
        runtime_cls = BaseRuntime

    arg = set_pea_parser().parse_args(['--runtime', 'thread'])
    mocker.patch.object(BaseRuntime, 'run_forever', bad_func)
    setup_spy = mocker.spy(BaseRuntime, 'setup')
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(BaseRuntime, 'cancel')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    with Pea1(arg):
        pass

    # teardown, setup should be called, cancel should not be called

    setup_spy.assert_called()
    teardown_spy.assert_called()
    run_spy.assert_called()
    cancel_spy.assert_not_called()


def test_base_runtime_bad_setup(mocker):
    class Pea1(BasePea):
        runtime_cls = BaseRuntime

    mocker.patch.object(BaseRuntime, 'setup', bad_func)
    setup_spy = mocker.spy(BaseRuntime, 'setup')
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(BaseRuntime, 'cancel')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    arg = set_pea_parser().parse_args(['--runtime', 'thread'])
    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass

    setup_spy.assert_called()
    teardown_spy.assert_not_called()
    run_spy.assert_not_called()
    cancel_spy.assert_not_called()  # 3s > .join(1), need to cancel
    # run_forever, teardown, cancel should not be called


def test_base_runtime_bad_teardown(mocker):
    class Pea1(BasePea):
        runtime_cls = BaseRuntime

    mocker.patch.object(BaseRuntime, 'run_forever', lambda x: time.sleep(3))
    mocker.patch.object(BaseRuntime, 'teardown', lambda x: bad_func)
    setup_spy = mocker.spy(BaseRuntime, 'setup')
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(BaseRuntime, 'cancel')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    arg = set_pea_parser().parse_args(['--runtime', 'thread'])
    with Pea1(arg):
        pass

    setup_spy.assert_called()
    teardown_spy.assert_called()
    run_spy.assert_called()
    cancel_spy.assert_called_once()  # 3s > .join(1), need to cancel

    # setup, run_forever cancel should all be called


def test_base_runtime_bad_cancel(mocker):
    class Pea1(BasePea):
        runtime_cls = BaseRuntime

    mocker.patch.object(BaseRuntime, 'run_forever', lambda x: time.sleep(3))
    mocker.patch.object(BaseRuntime, 'cancel', bad_func)

    setup_spy = mocker.spy(BaseRuntime, 'setup')
    teardown_spy = mocker.spy(BaseRuntime, 'teardown')
    cancel_spy = mocker.spy(BaseRuntime, 'cancel')
    run_spy = mocker.spy(BaseRuntime, 'run_forever')

    arg = set_pea_parser().parse_args(['--runtime', 'thread'])
    with Pea1(arg):
        pass

    setup_spy.assert_called()
    teardown_spy.assert_called()
    run_spy.assert_called()
    cancel_spy.assert_called_once()

    # setup, run_forever cancel should all be called


def test_zed_runtime():
    class Pea1(BasePea):
        runtime_cls = ZEDRuntime

    arg = set_pea_parser().parse_args([])
    with Pea1(arg):
        pass


@pytest.mark.parametrize('cls', [GRPCRuntime, RESTRuntime])
@pytest.mark.parametrize('runtime', ['thread', 'process'])
def test_gateway_runtime(cls, runtime):
    class Pea1(BasePea):
        runtime_cls = cls

    arg = set_gateway_parser().parse_args(['--runtime', runtime])
    with Pea1(arg):
        pass


def test_container_runtime_bad_entrypoint():
    class Pea1(BasePea):
        runtime_cls = ContainerRuntime

    # without correct entrypoint this will fail
    arg = set_pea_parser().parse_args(['--uses', 'jinaai/jina:test-pip',
                                       ])
    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass


def test_container_runtime_good_entrypoint():
    class Pea1(BasePea):
        runtime_cls = ContainerRuntime

    # without correct entrypoint this will fail
    arg = set_pea_parser().parse_args(['--uses', 'jinaai/jina:test-pip',
                                       '--entrypoint', 'jina pod'])
    with Pea1(arg):
        pass


@pytest.mark.parametrize('runtime', ['thread', 'process'])
@pytest.mark.parametrize('cls, parser, args', [(ContainerRuntime, set_pea_parser,
                                                ['--uses', 'jinaai/jina:test-pip',
                                                 '--entrypoint', 'jina pod']),
                                               (RESTRuntime, set_gateway_parser, []),
                                               (ZEDRuntime, set_pea_parser, [])])
def test_runtime_thread_process(runtime, cls, parser, args):
    class Pea1(BasePea):
        runtime_cls = cls

    args.extend(['--runtime', runtime])
    arg = parser().parse_args(args)
    with Pea1(arg):
        pass
