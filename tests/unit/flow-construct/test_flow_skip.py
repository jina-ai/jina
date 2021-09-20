import pytest

from jina import Flow, Executor, requests, Document
from jina.enums import OnErrorStrategy
from jina.proto import jina_pb2
from tests import validate_callback


class DummyCrafterSkip(Executor):
    @requests
    def craft(self, *args, **kwargs):
        return 1 / 0


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_bad_flow_skip_handle(mocker, protocol):
    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code >= jina_pb2.StatusProto.ERROR
        ]
        assert len(bad_routes) == 3
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].pod == 'r1/ZEDRuntime'
        assert bad_routes[1].pod == 'r2/ZEDRuntime'
        assert bad_routes[1].status.code == jina_pb2.StatusProto.ERROR_CHAINED
        assert bad_routes[2].pod == 'r3/ZEDRuntime'
        assert bad_routes[2].status.code == jina_pb2.StatusProto.ERROR_CHAINED

    f = (
        Flow(protocol=protocol, on_error_strategy=OnErrorStrategy.SKIP_HANDLE)
        .add(name='r1', uses='!DummyCrafterSkip')
        .add(name='r2')
        .add(name='r3')
    )

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_bad_flow_skip_handle_join(mocker, protocol):
    """When skipmode is set to handle, reduce driver wont work anymore"""

    def validate(req):
        bad_routes = [
            r for r in req.routes if r.status.code >= jina_pb2.StatusProto.ERROR
        ]
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
        assert bad_routes[0].pod == 'r1/ZEDRuntime'
        assert bad_routes[-1].pod == 'joiner/ZEDRuntime'
        assert bad_routes[-1].status.code == jina_pb2.StatusProto.ERROR_CHAINED
        assert bad_routes[-1].status.exception.name == ''

    f = (
        Flow(protocol=protocol, on_error_strategy=OnErrorStrategy.SKIP_HANDLE)
        .add(name='r1', uses=DummyCrafterSkip)
        .add(name='r2')
        .add(name='r3', needs='r1')
        .needs(['r3', 'r2'])
    )

    on_error_mock = mocker.Mock()

    # always test two times, make sure the flow still works after it fails on the first
    with f:
        f.index([Document(text='abbcs'), Document(text='efgh')], on_error=on_error_mock)

    validate_callback(on_error_mock, validate)
