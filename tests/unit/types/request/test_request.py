import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina.excepts import BadRequestType
from jina.helper import get_random_identity
from jina.proto import jina_pb2
from jina.types.request import Request
from jina.types.sets.document import DocumentSet
from jina.types.sets.querylang import QueryLangSet


@pytest.fixture(scope='function')
def req():
    r = jina_pb2.RequestProto()
    r.request_id = get_random_identity()
    r.index.docs.add()
    return r


def test_init(req):
    assert Request(request=None)
    assert Request(request=req, copy=True)
    assert Request(request=req, copy=False)
    assert Request(request=MessageToDict(req))
    assert Request(request=MessageToJson(req))


def test_init_fail():
    with pytest.raises(BadRequestType):
        Request(request=5)


def test_docs(req):
    request = Request(request=req, copy=False)
    docs = request.docs
    assert request.is_used
    assert isinstance(docs, DocumentSet)
    assert len(docs) == 1


def test_groundtruth(req):
    request = Request(request=req, copy=False)
    groundtruths = request.groundtruths
    assert request.is_used
    assert isinstance(groundtruths, DocumentSet)
    assert len(groundtruths) == 0


def test_request_type_set_get(req):
    request = Request(request=req, copy=False)
    request.request_type = 'search'
    assert request.request_type == 'SearchRequestProto'


def test_request_type_set_get_fail(req):
    request = Request(request=req, copy=False)
    with pytest.raises(ValueError):
        request.request_type = 'random'


def test_queryset(req):
    request = Request(request=req, copy=False)
    queryset = request.queryset
    assert request.is_used
    assert isinstance(queryset, QueryLangSet)


def test_command(req):
    request = Request(request=req, copy=False)
    cmd = request.command
    assert request.is_used
    assert cmd
    assert isinstance(cmd, str)


def test_as_pb_object(req):
    request = Request(request=req)
    request.as_pb_object
    assert request.is_used
    request = Request(request=None)
    assert request.as_pb_object
    assert request.is_used


def test_as_json_str(req):
    request = Request(request=req)
    assert isinstance(request.to_json(), str)
    request = Request(request=None)
    assert isinstance(request.to_json(), str)
