import numpy as np
import pytest

from jina import Flow, Executor, requests, Document
from jina.proto import jina_pb2
from jina.types.document.generators import from_ndarray
from tests import validate_callback


class DummyCrafterExcept(Executor):
    @requests
    def craft(self, *args, **kwargs):
        return 1 / 0


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_bad_flow(mocker, protocol):
    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1/ZEDRuntime'

    from jina import Executor, requests

    class BadExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            raise NotImplementedError

    f = (
        Flow(protocol=protocol)
        .add(name='r1', uses=BadExecutor)
        .add(name='r2')
        .add(name='r3')
    )

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow test_bad_flow_customizedstill works after it fails on the first
    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_bad_flow_customized(mocker, protocol):
    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r2/ZEDRuntime'
        assert bad_routes[0].status.exception.name == 'ZeroDivisionError'

    f = (
        Flow(protocol=protocol)
        .add(name='r1')
        .add(name='r2', uses='!DummyCrafterExcept')
        .add(name='r3', uses='!BaseExecutor')
    )

    with f:
        pass

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_except_with_parallel(mocker, protocol):
    from jina import Executor, Flow, requests

    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            raise NotImplementedError

    def validate(req):
        assert req.status.code == jina_pb2.StatusProto.ERROR
        err_routes = [
            r.status for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert len(err_routes) == 2
        assert err_routes[0].exception.executor == 'DummyCrafterExcept'
        assert err_routes[1].exception.executor == 'MyExecutor'
        assert err_routes[0].exception.name == 'ZeroDivisionError'
        assert err_routes[1].exception.name == 'NotImplementedError'

    f = (
        Flow(protocol=protocol)
        .add(name='r1')
        .add(name='r2', uses=DummyCrafterExcept, parallel=3)
        .add(name='r3', uses=MyExecutor)
    )

    with f:
        pass

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_on_error_callback(mocker, protocol):
    def validate1():
        raise NotImplementedError

    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            raise NotImplementedError

    def validate2(x, *args):
        x = x.routes
        assert len(x) == 4  # gateway, r1, r3, gateway
        badones = [r for r in x if r.status.code == jina_pb2.StatusProto.ERROR]
        assert badones[0].pod == 'r3/ZEDRuntime'

    f = Flow(protocol=protocol).add(name='r1').add(name='r3', uses=MyExecutor)

    on_error_mock = mocker.Mock()

    with f:
        f.index(
            [Document(text='abbcs'), Document(text='efgh')],
            on_done=validate1,
            on_error=on_error_mock,
        )

    validate_callback(on_error_mock, validate2)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_no_error_callback(mocker, protocol):
    def validate2():
        raise NotImplementedError

    def validate1(x, *args):
        pass

    f = Flow(protocol=protocol).add(name='r1').add(name='r3')

    response_mock = mocker.Mock()
    on_error_mock = mocker.Mock()

    with f:
        f.index(
            [Document(text='abbcs'), Document(text='efgh')],
            on_done=response_mock,
            on_error=on_error_mock,
        )

    validate_callback(response_mock, validate1)
    on_error_mock.assert_not_called()


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_on_callback(protocol):
    f = Flow(protocol=protocol).add()
    hit = []

    def f1(*args):
        hit.append('done')

    def f2(*args):
        hit.append('error')

    def f3(*args):
        hit.append('always')

    with f:
        f.index(
            from_ndarray(np.random.random([10, 10])),
            on_done=f1,
            on_error=f2,
            on_always=f3,
        )

    assert hit == ['done', 'always']

    hit.clear()


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_on_error_callback(protocol):
    class DummyCrafterNotImplemented(Executor):
        @requests
        def craft(self, text, *args, **kwargs):
            raise NotImplementedError

    f = Flow(protocol=protocol).add(uses='!DummyCrafterNotImplemented')
    hit = []

    def f1(*args):
        hit.append('done')

    def f2(*args):
        hit.append('error')

    def f3(*args):
        hit.append('always')

    with f:
        f.index(
            from_ndarray(np.random.random([10, 10])),
            on_done=f1,
            on_error=f2,
            on_always=f3,
        )

    assert hit == ['error', 'always']

    hit.clear()


@pytest.mark.timeout(10)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_startup_exception_not_hanging(protocol):
    class ExceptionExecutor(Executor):
        def __init__(self, *args, **kwargs):
            raise Exception

    f = Flow(protocol=protocol).add(uses=ExceptionExecutor)
    from jina.excepts import RuntimeFailToStart

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass


@pytest.mark.timeout(10)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_startup_exception_not_hanging2(protocol):
    class ExceptionExecutor(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            raise Exception

    f = Flow(protocol=protocol).add(uses=ExceptionExecutor)
    from jina.excepts import RuntimeFailToStart

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass
