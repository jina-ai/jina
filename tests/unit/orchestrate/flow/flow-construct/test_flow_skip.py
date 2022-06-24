import pytest

from jina import Document, Executor, Flow, requests
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
        assert len(bad_routes) == 1
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].executor == 'r1'

    f = (
        Flow(protocol=protocol)
        .add(name='r1', uses=DummyCrafterSkip)
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
        assert len(bad_routes) == 1
        assert req.status.code == jina_pb2.StatusProto.ERROR
        assert bad_routes[0].executor == 'r1'

    f = (
        Flow(protocol=protocol)
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
