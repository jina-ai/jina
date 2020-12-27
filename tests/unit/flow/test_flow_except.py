import numpy as np

from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from jina.proto import jina_pb2


class DummyCrafter(BaseCrafter):
    def craft(self, *args, **kwargs):
        return 1 / 0


def test_bad_flow(mocker):
    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1'

    f = (Flow().add(name='r1', uses='!BaseCrafter')
         .add(name='r2', uses='!BaseEncoder')
         .add(name='r3', uses='!BaseEncoder'))

    on_error_mock = mocker.Mock(wrap=validate)
    on_error_mock_2 = mocker.Mock(wrap=validate)

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock)
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock_2)

    on_error_mock.assert_called()
    on_error_mock_2.assert_called()


def test_bad_flow_customized(mocker):
    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR]
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r2'
        assert bad_routes[0].status.exception.name == 'ZeroDivisionError'

    f = (Flow().add(name='r1')
         .add(name='r2', uses='!DummyCrafter')
         .add(name='r3', uses='!BaseEncoder'))

    with f:
        pass

    on_error_mock = mocker.Mock(wrap=validate)
    on_error_mock_2 = mocker.Mock(wrap=validate)

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock)
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock_2)

    on_error_mock.assert_called()
    on_error_mock_2.assert_called()


def test_except_with_parallel(mocker):
    def validate(req):
        assert req.status.code == jina_pb2.StatusProto.ERROR
        err_routes = [r.status for r in req.routes if r.status.code == jina_pb2.StatusProto.ERROR]
        assert len(err_routes) == 2
        assert err_routes[0].exception.executor == 'DummyCrafter'
        assert err_routes[1].exception.executor == 'BaseEncoder'
        assert err_routes[0].exception.name == 'ZeroDivisionError'
        assert err_routes[1].exception.name == 'NotImplementedError'

    f = (Flow().add(name='r1')
         .add(name='r2', uses='!DummyCrafter', parallel=3)
         .add(name='r3', uses='!BaseEncoder'))

    with f:
        pass

    on_error_mock = mocker.Mock(wrap=validate)
    on_error_mock_2 = mocker.Mock(wrap=validate)

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock)
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock_2)

    on_error_mock.assert_called()
    on_error_mock_2.assert_called()


def test_on_error_callback(mocker):
    def validate1():
        raise NotImplementedError

    def validate2(x, *args):
        x = x.routes
        assert len(x) == 4  # gateway, r1, r3, gateway
        badones = [r for r in x if r.status.code == jina_pb2.StatusProto.ERROR]
        assert badones[0].pod == 'r3'

    f = (Flow().add(name='r1')
         .add(name='r3', uses='!BaseEncoder'))

    on_error_mock = mocker.Mock(wrap=validate2)

    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_done=validate1, on_error=on_error_mock)

    on_error_mock.assert_called()


def test_no_error_callback(mocker):
    def validate2():
        raise NotImplementedError

    def validate1(x, *args):
        pass

    f = (Flow().add(name='r1')
         .add(name='r3'))

    response_mock = mocker.Mock(wrap=validate1)
    on_error_mock = mocker.Mock(wrap=validate2)

    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_done=response_mock, on_error=on_error_mock)

    response_mock.assert_called()
    on_error_mock.assert_not_called()


def test_flow_on_callback():
    f = Flow().add()
    hit = []

    def f1(*args):
        hit.append('done')

    def f2(*args):
        hit.append('error')

    def f3(*args):
        hit.append('always')

    with f:
        f.index(np.random.random([10, 10]),
                on_done=f1, on_error=f2, on_always=f3)

    assert hit == ['done', 'always']

    hit.clear()


def test_flow_on_error_callback():

    class DummyCrafter(BaseCrafter):
        def craft(self, *args, **kwargs):
            raise NotImplementedError

    f = Flow().add(uses='DummyCrafter')
    hit = []

    def f1(*args):
        hit.append('done')

    def f2(*args):
        hit.append('error')

    def f3(*args):
        hit.append('always')

    with f:
        f.index(np.random.random([10, 10]),
                on_done=f1, on_error=f2, on_always=f3)

    assert hit == ['error', 'always']

    hit.clear()
