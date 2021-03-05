import pytest

import numpy as np

from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from jina.proto import jina_pb2

from tests import validate_callback


class DummyCrafter(BaseCrafter):
    def craft(self, *args, **kwargs):
        return 1 / 0


@pytest.mark.parametrize('restful', [False, True])
def test_bad_flow(mocker, restful):
    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1/ZEDRuntime'

    f = (
        Flow(restful=restful)
        .add(name='r1', uses='!BaseCrafter')
        .add(name='r2', uses='!BaseEncoder')
        .add(name='r3', uses='!BaseEncoder')
    )

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index(['abbcs', 'efgh'], on_error=on_error_mock)
        f.index(['abbcs', 'efgh'], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('restful', [False, True])
def test_bad_flow_customized(mocker, restful):
    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r2/ZEDRuntime'
        assert bad_routes[0].status.exception.name == 'ZeroDivisionError'

    f = (
        Flow(restful=restful)
        .add(name='r1')
        .add(name='r2', uses='!DummyCrafter')
        .add(name='r3', uses='!BaseEncoder')
    )

    with f:
        pass

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index(['abbcs', 'efgh'], on_error=on_error_mock)
        f.index(['abbcs', 'efgh'], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('restful', [False, True])
def test_except_with_parallel(mocker, restful):
    def validate(req):
        assert req.status.code == jina_pb2.StatusProto.ERROR
        err_routes = [
            r.status for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR
        ]
        assert len(err_routes) == 2
        assert err_routes[0].exception.executor == 'DummyCrafter'
        assert err_routes[1].exception.executor == 'BaseEncoder'
        assert err_routes[0].exception.name == 'ZeroDivisionError'
        assert err_routes[1].exception.name == 'NotImplementedError'

    f = (
        Flow(restful=restful)
        .add(name='r1')
        .add(name='r2', uses='!DummyCrafter', parallel=3)
        .add(name='r3', uses='!BaseEncoder')
    )

    with f:
        pass

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index(['abbcs', 'efgh'], on_error=on_error_mock)
        f.index(['abbcs', 'efgh'], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('restful', [False, True])
def test_on_error_callback(mocker, restful):
    def validate1():
        raise NotImplementedError

    def validate2(x, *args):
        x = x.routes
        assert len(x) == 4  # gateway, r1, r3, gateway
        badones = [r for r in x if r.status.code == jina_pb2.StatusProto.ERROR]
        assert badones[0].pod == 'r3/ZEDRuntime'

    f = Flow(restful=restful).add(name='r1').add(name='r3', uses='!BaseEncoder')

    on_error_mock = mocker.Mock()

    with f:
        f.index(['abbcs', 'efgh'], on_done=validate1, on_error=on_error_mock)

    validate_callback(on_error_mock, validate2)


@pytest.mark.parametrize('restful', [False, True])
def test_no_error_callback(mocker, restful):
    def validate2():
        raise NotImplementedError

    def validate1(x, *args):
        pass

    f = Flow(restful=restful).add(name='r1').add(name='r3')

    response_mock = mocker.Mock()
    on_error_mock = mocker.Mock()

    with f:
        f.index(['abbcs', 'efgh'], on_done=response_mock, on_error=on_error_mock)

    validate_callback(response_mock, validate1)
    on_error_mock.assert_not_called()


@pytest.mark.parametrize('restful', [False, True])
def test_flow_on_callback(restful):
    f = Flow(restful=restful).add()
    hit = []

    def f1(*args):
        hit.append('done')

    def f2(*args):
        hit.append('error')

    def f3(*args):
        hit.append('always')

    with f:
        f.index(np.random.random([10, 10]), on_done=f1, on_error=f2, on_always=f3)

    assert hit == ['done', 'always']

    hit.clear()


@pytest.mark.parametrize('restful', [False, True])
def test_flow_on_error_callback(restful):
    class DummyCrafter(BaseCrafter):
        def craft(self, *args, **kwargs):
            raise NotImplementedError

    f = Flow(restful=restful).add(uses='DummyCrafter')
    hit = []

    def f1(*args):
        hit.append('done')

    def f2(*args):
        hit.append('error')

    def f3(*args):
        hit.append('always')

    with f:
        f.index(np.random.random([10, 10]), on_done=f1, on_error=f2, on_always=f3)

    assert hit == ['error', 'always']

    hit.clear()
