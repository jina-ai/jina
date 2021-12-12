import copy

import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina import Document
from jina.excepts import BadRequestType
from jina.helper import random_identity
from jina.proto import jina_pb2
from jina.proto.jina_pb2 import DocumentArrayProto
from jina.types.arrays.document import DocumentArray
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest, Response


@pytest.fixture(scope='function')
def req():
    r = jina_pb2.DataRequestProto()
    r.header.request_id = random_identity()
    r.data.docs.add()
    return r


@pytest.fixture(scope='function')
def control_req():
    r = jina_pb2.ControlRequestProto()
    r.header.request_id = random_identity()
    return r


def test_init(req):
    assert DataRequest(request=None)
    assert DataRequest(request=req)
    assert DataRequest(request=MessageToDict(req))
    assert DataRequest(request=MessageToJson(req))


def test_init_fail():
    with pytest.raises(BadRequestType):
        DataRequest(request=5)


def test_docs(req):
    request = DataRequest(request=req)
    docs = request.docs
    assert isinstance(docs, DocumentArray)
    assert len(docs) == 1


def test_docs_operations():
    req = DataRequest()
    assert not req.docs

    req.docs.append(Document())
    assert len(req.docs) == 1

    req.docs.clear()
    assert not req.docs

    req.docs.extend(DocumentArray([Document(), Document()]))
    assert len(req.docs) == 2


def test_copy(req):
    request = DataRequest(req)
    copied_req = copy.deepcopy(request)
    assert type(request) == type(copied_req)
    assert request == copied_req
    assert len(request.docs) == len(copied_req.docs)
    request.docs.append(Document())
    assert len(request.docs) != len(copied_req.docs)


def test_groundtruth(req):
    request = DataRequest(request=req)
    groundtruths = request.groundtruths
    assert isinstance(groundtruths, DocumentArray)
    assert len(groundtruths) == 0


def test_data_backwards_compatibility(req):
    req = DataRequest(request=req)
    assert len(req.data.docs) == 1
    assert len(req.data.groundtruths) == 0
    assert len(req.data.docs) == len(req.docs)
    assert len(req.data.groundtruths) == len(req.groundtruths)


def test_command(control_req):
    request = ControlRequest(request=control_req)
    cmd = request.command
    assert cmd
    assert isinstance(cmd, str)


def test_as_pb_object(req):
    request = DataRequest(request=None)
    assert request.proto


def test_as_json_str(req):
    request = DataRequest(request=req)
    assert isinstance(request.json(), str)
    request = DataRequest(request=None)
    assert isinstance(request.json(), str)


def test_access_header(req):
    request = DataRequest(request=req)
    assert request.header == req.header


def test_as_response(req):
    request = DataRequest(request=req)
    response = request.response
    assert isinstance(response, Response)
    assert isinstance(response, DataRequest)
    assert response._pb_body == request._pb_body
