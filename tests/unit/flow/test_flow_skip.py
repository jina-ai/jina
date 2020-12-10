from jina.enums import SkipOnErrorType
from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from jina.proto import jina_pb2


class DummyCrafter(BaseCrafter):
    def craft(self, *args, **kwargs):
        return 1 / 0


def test_bad_flow_skip_handle(mocker):
    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code >= jina_pb2.StatusProto.ERROR]
        assert len(bad_routes) == 3
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1'
        assert bad_routes[1].pod == 'r2'
        assert bad_routes[1].status.code == jina_pb2.StatusProto.ERROR_CHAINED
        assert bad_routes[2].pod == 'r3'
        assert bad_routes[2].status.code == jina_pb2.StatusProto.ERROR_CHAINED

    f = (Flow(skip_on_error=SkipOnErrorType.HANDLE).add(name='r1', uses='DummyCrafter')
         .add(name='r2')
         .add(name='r3'))

    on_error_mock = mocker.Mock(wrap=validate)

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock)

    on_error_mock.assert_called()


def test_bad_flow_skip_handle_join(mocker):
    """When skipmode is set to handle, reduce driver wont work anymore"""

    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code >= jina_pb2.StatusProto.ERROR]
        # NOTE: tricky one:
        # the bad pods should be r1, either r2 or r3, joiner, gateway
        # the reason here is when skip strategy set to handle, then
        # driver is skipped, including the reduce driver in `joiner`.
        # when `joiner` doesn't do reduce anymore, r2 & r3 becomes first
        # comes first serves, therefore only oneof them will show up in the route table
        # finally, as joiner does not to reduce anymore, gateway will receive a
        # num_part=[1,2] message and raise an error
        assert len(bad_routes) == 4
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1'
        assert bad_routes[-1].pod == 'gateway'
        assert bad_routes[-1].status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[-1].status.exception.name == 'GatewayPartialMessage'

    f = (Flow(skip_on_error=SkipOnErrorType.HANDLE).add(name='r1', uses='DummyCrafter')
         .add(name='r2')
         .add(name='r3', needs='r1')
         .needs(['r3', 'r2']))

    on_error_mock = mocker.Mock(wrap=validate)

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock)

    on_error_mock.assert_called()


def test_bad_flow_skip_exec(mocker):
    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code >= jina_pb2.StatusProto.ERROR]
        assert len(bad_routes) == 1
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1'

    f = (Flow(skip_on_error=SkipOnErrorType.EXECUTOR).add(name='r1', uses='DummyCrafter')
         .add(name='r2')
         .add(name='r3'))

    on_error_mock = mocker.Mock(wrap=validate)

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock)

    on_error_mock.assert_called()


def test_bad_flow_skip_exec_join(mocker):
    """Make sure the exception wont affect the gather/reduce ops"""

    def validate(req):
        bad_routes = [r for r in req.routes if r.status.code >= jina_pb2.StatusProto.ERROR]
        assert len(bad_routes) == 1
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1'

    f = (Flow(skip_on_error=SkipOnErrorType.EXECUTOR).add(name='r1', uses='DummyCrafter')
         .add(name='r2')
         .add(name='r3', needs='r1')
         .needs(['r3', 'r2']))

    on_error_mock = mocker.Mock(wrap=validate)

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index_lines(lines=['abbcs', 'efgh'], on_error=on_error_mock)

    on_error_mock.assert_called()
