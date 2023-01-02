import os
import time

import numpy as np
import pytest
from docarray.document.generators import from_ndarray

from jina import Document, Executor, Flow, requests
from jina.excepts import BadServer, RuntimeFailToStart
from jina.proto import jina_pb2
from tests import validate_callback


class DummyCrafterExcept(Executor):
    @requests
    def craft(self, *args, **kwargs):
        return 1 / 0


class BadExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError


@pytest.mark.parametrize('protocol', ['http', 'grpc', 'websocket'])
def test_bad_flow(mocker, protocol):
    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].executor == 'r1'

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


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_bad_flow_customized(mocker, protocol):
    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].executor == 'r2'
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


class NotImplementedExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        raise NotImplementedError


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_except_with_shards(mocker, protocol):
    def validate(req):
        assert req.status.code == jina_pb2.StatusProto.ERROR
        err_routes = [
            r.status for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert len(err_routes) == 1
        assert err_routes[0].exception.executor == 'DummyCrafterExcept'
        assert err_routes[0].exception.name == 'ZeroDivisionError'

    f = (
        Flow(protocol=protocol)
        .add(name='r1')
        .add(name='r2', uses=DummyCrafterExcept, shards=3)
        .add(name='r3', uses=NotImplementedExecutor)
    )

    with f:
        pass

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('protocol', ['grpc', 'websocket', 'http'])
def test_on_error_callback(mocker, protocol):
    def validate(x, *args):
        x = x.routes
        assert len(x) == 3  # gateway, r1, r3, gateway
        badones = [r for r in x if r.status.code == jina_pb2.StatusProto.ERROR]
        assert badones[0].executor == 'r3'

    f = (
        Flow(protocol=protocol)
        .add(name='r1')
        .add(name='r3', uses=NotImplementedExecutor)
    )

    on_error_mock = mocker.Mock()

    with f:
        f.index(
            [Document(text='abbcs'), Document(text='efgh')],
            on_error=on_error_mock,
        )

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_no_error_callback(mocker, protocol):
    f = Flow(protocol=protocol).add(name='r1').add(name='r3')

    on_error_mock = mocker.Mock()

    with f:
        results = f.index(
            [Document(text='abbcs'), Document(text='efgh')],
            on_error=on_error_mock,
        )

    assert len(results) > 0
    on_error_mock.assert_not_called()


@pytest.mark.parametrize('protocol', ['websocket', 'http', 'grpc'])
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


class DummyCrafterNotImplemented(Executor):
    @requests
    def craft(self, *args, **kwargs):
        raise NotImplementedError


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_on_error_callback(protocol):
    f = Flow(protocol=protocol).add(uses=DummyCrafterNotImplemented)
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


class ExceptionExecutor1(Executor):
    def __init__(self, *args, **kwargs):
        raise Exception


@pytest.mark.repeat(10)
@pytest.mark.timeout(10)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_startup_exception_not_hanging1(protocol):
    f = Flow(protocol=protocol).add(uses=ExceptionExecutor1)
    from jina.excepts import RuntimeFailToStart

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass


class ExceptionExecutor2(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise Exception


@pytest.mark.repeat(10)
@pytest.mark.timeout(10)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_startup_exception_not_hanging2(protocol):
    f = Flow(protocol=protocol).add(uses=ExceptionExecutor2)
    from jina.excepts import RuntimeFailToStart

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass


@pytest.mark.timeout(10)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_startup_exception_not_hanging_filenotfound(protocol):
    f = Flow(protocol=protocol).add(uses='doesntexist.yml')
    from jina.excepts import RuntimeFailToStart

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass


@pytest.mark.timeout(10)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_flow_startup_exception_not_hanging_invalid_config(protocol):
    this_file = os.path.dirname(os.path.abspath(__file__))
    f = Flow(protocol=protocol).add(
        name='importErrorExecutor',
        uses=this_file,
    )

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass


def test_flow_does_not_import_exec_dependencies():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    f = Flow().add(
        name='importErrorExecutor',
        uses=os.path.join(cur_dir, 'executor-invalid-import/config.yml'),
    )

    with pytest.raises(RuntimeFailToStart):
        with f:
            pass


class TimeoutSlowExecutor(Executor):
    @requests(on='/index')
    def foo(self, *args, **kwargs):
        time.sleep(1.5)


@pytest.mark.timeout(50)
def test_flow_timeout_send():
    f = Flow().add(uses=TimeoutSlowExecutor)

    with f:
        f.index([Document()])

    f = Flow(timeout_send=3000).add(uses=TimeoutSlowExecutor)

    with f:
        f.index([Document()])

    f = Flow(timeout_send=100).add(uses=TimeoutSlowExecutor)

    with f:
        with pytest.raises(Exception):
            f.index([Document()])


def test_flow_head_runtime_failure(monkeypatch):
    from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler

    def fail(*args, **kwargs):
        raise NotImplementedError('Intentional error')

    monkeypatch.setattr(WorkerRequestHandler, 'merge_routes', fail)

    with Flow().add(shards=2) as f:
        with pytest.raises(BadServer) as err_info:
            f.index([Document(text='abbcs')])
    err_text = err_info.value.args[0].status.description
    assert 'NotImplementedError' in err_text
    assert 'Intentional' in err_text and 'error' in err_text
