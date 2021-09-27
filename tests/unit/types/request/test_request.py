import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina.excepts import BadRequestType
from jina.helper import random_identity
from jina.proto import jina_pb2
from jina.types.arrays.document import DocumentArray
from jina.types.request import Request, Response


@pytest.fixture(scope='function')
def req():
    r = jina_pb2.RequestProto()
    r.request_id = random_identity()
    r.data.docs.add()
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
    request = Request(request=req, copy=False).as_typed_request('data')
    docs = request.docs
    assert request.is_decompressed
    assert isinstance(docs, DocumentArray)
    assert len(docs) == 1


def test_groundtruth(req):
    request = Request(request=req, copy=False).as_typed_request('data')
    groundtruths = request.groundtruths
    assert request.is_decompressed
    assert isinstance(groundtruths, DocumentArray)
    assert len(groundtruths) == 0


def test_request_type_set_get(req):
    request = Request(request=req, copy=False).as_typed_request('data')
    assert request.request_type == 'DataRequestProto'


def test_request_type_set_get_fail(req):
    with pytest.raises(TypeError):
        Request(request=req, copy=False).as_typed_request('random')


def test_command(req):
    request = Request(request=req, copy=False).as_typed_request('control')
    cmd = request.command
    assert request.is_decompressed
    assert cmd
    assert isinstance(cmd, str)


def test_as_pb_object(req):
    request = Request(request=req)
    request.proto
    assert request.is_decompressed
    request = Request(request=None)
    assert request.proto
    assert request.is_decompressed


def test_as_json_str(req):
    request = Request(request=req)
    assert isinstance(request.json(), str)
    request = Request(request=None)
    assert isinstance(request.json(), str)


def test_access_header(req):
    request = Request(request=req)
    assert request.header == req.header


def test_as_response(req):
    request = Request(request=req)
    response = request.as_response()
    assert isinstance(response, Response)
    assert isinstance(response, Request)
    assert response._pb_body == request._pb_body
