import copy

import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from docarray.proto.docarray_pb2 import DocumentProto
from jina.excepts import BadRequestType
from jina.helper import random_identity
from jina.proto import jina_pb2
from docarray import DocumentArray, Document
from jina.proto.serializer import DataRequestProto
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest, Response
from tests import random_docs


@pytest.fixture(scope='function')
def req():
    r = jina_pb2.DataRequestProto()
    r.header.request_id = random_identity()
    r.data.docs.docs.add()
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


def test_copy(req):
    request = DataRequest(req)
    copied_req = copy.deepcopy(request)
    assert type(request) == type(copied_req)
    assert request == copied_req
    assert len(request.docs) == len(copied_req.docs)


def test_data_backwards_compatibility(req):
    req = DataRequest(request=req)
    assert len(req.data.docs) == 1
    assert len(req.data.docs) == len(req.docs)


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


def test_lazy_serialization():
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequestProto.FromString(byte_array)
    assert not deserialized_request.is_decompressed
    assert len(deserialized_request.docs) == doc_count
    assert deserialized_request.docs == r.docs
    assert deserialized_request.is_decompressed


def test_lazy_serialization_bytes():
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs_bytes = da.to_bytes()
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequestProto.FromString(byte_array)
    assert not deserialized_request.is_decompressed
    assert len(deserialized_request.docs) == doc_count
    assert deserialized_request.docs == r.docs
    assert deserialized_request.is_decompressed


def test_status():
    r = DataRequest()
    r.docs.extend([Document()])
    r.add_exception(ValueError('intentional_error'))
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequestProto.FromString(byte_array)
    assert not deserialized_request.is_decompressed
    assert deserialized_request.status.code == jina_pb2.StatusProto.ERROR
    assert deserialized_request.is_decompressed
