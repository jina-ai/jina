import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina.excepts import BadRequestType
from jina.proto import jina_pb2
from jina.types.request.status import StatusMessage


@pytest.fixture(scope='function')
def status_pb():
    return jina_pb2.StatusProto()


def test_init(status_pb):
    assert StatusMessage(status_object=None)
    assert StatusMessage(status_object=status_pb)
    assert StatusMessage(status_object=MessageToDict(status_pb))
    assert StatusMessage(status_object=MessageToJson(status_pb))


def test_init_fail():
    with pytest.raises(BadRequestType):
        StatusMessage(status_object=5)


@pytest.mark.parametrize(
    'status_code', [jina_pb2.StatusProto.SUCCESS, jina_pb2.StatusProto.ERROR]
)
def test_set_code(status_code):
    status = StatusMessage()
    status.set_code(status_code)
    assert status.proto.code == status_code


def test_set_exception():
    status = StatusMessage()
    exc = Exception('exception code')
    status.set_exception(exc)
    assert status.proto.code == jina_pb2.StatusProto.ERROR
    assert status.proto.description == repr(exc)
    assert status.proto.exception.name == exc.__class__.__name__
