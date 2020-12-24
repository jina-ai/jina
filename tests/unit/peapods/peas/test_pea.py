import pytest

from jina.parser import set_pea_parser
from jina.peapods.peas import BasePea
from jina.excepts import DriverError, NoDriverForRequest, ExecutorFailToLoad, EventLoopError, RequestLoopEnd


class MockExceptionRequestLoopPea(BasePea):

    def __init__(self, args, exception_class):
        super().__init__(args)
        self.exception = exception_class
        self.properly_closed = False

    def request_loop(self, is_ready_event):
        raise self.exception

    def _teardown(self):
        super()._teardown()
        self.properly_closed = True


def pea_exception_request_loop_factory():
    class MockExceptionRequestLoopPeaFactory:
        def create(self, exception_class):
            args = set_pea_parser().parse_args([])
            return MockExceptionRequestLoopPea(args, exception_class)

    return MockExceptionRequestLoopPeaFactory()


class MockExceptionCallbackPea(BasePea):

    def __init__(self, args, exception_class):
        super().__init__(args)
        self.exception = exception_class
        self.properly_closed = False

    def _callback(self, msg):
        raise self.exception

    def _teardown(self):
        super()._teardown()
        self.properly_closed = True


def pea_exception_callback_factory():
    class MockExceptionCallbackPeaFactory:
        def create(self, exception_class):
            args = set_pea_parser().parse_args([])
            return MockExceptionCallbackPea(args, exception_class)

    return MockExceptionCallbackPeaFactory()


class MockExceptionLoadExecutorPea(BasePea):

    def __init__(self, args, exception_class):
        super().__init__(args)
        self.exception = exception_class
        self.properly_closed = False

    def _load_executor(self):
        raise self.exception

    def _teardown(self):
        super()._teardown()
        self.properly_closed = True


@pytest.fixture
def pea_exception_load_executor_factory():
    class MockExceptionLoadExecutorPeaFactory:
        def create(self, exception_class):
            args = set_pea_parser().parse_args([])
            return MockExceptionLoadExecutorPea(args, exception_class)

    return MockExceptionLoadExecutorPeaFactory()


def test_pea_context_load_executor():
    args = set_pea_parser().parse_args([])
    pea = BasePea(args)
    assert not hasattr(pea, 'executor')
    with pea:
        assert pea.executor


@pytest.mark.parametrize('factory', [pea_exception_request_loop_factory,
                                     pea_exception_callback_factory])
@pytest.mark.parametrize('exception_class', [RuntimeError, SystemError,
                                             KeyboardInterrupt, DriverError, NoDriverForRequest,
                                             NotImplementedError, ExecutorFailToLoad, EventLoopError,
                                             RequestLoopEnd])
def test_pea_proper_terminate(factory, exception_class):
    pea = factory().create(exception_class)
    with pea:
        pass
    assert pea.properly_closed


@pytest.mark.parametrize('exception_class', [ExecutorFailToLoad, RuntimeError, SystemError,
                                             DriverError, NoDriverForRequest,
                                             NotImplementedError])
def test_pea_proper_terminate_when_load_fails(pea_exception_load_executor_factory, exception_class):
    with pytest.raises(exception_class):
        pea = pea_exception_load_executor_factory.create(exception_class)
        with pea:
            pass

    # exception happens in __enter__
    assert not pea.properly_closed
