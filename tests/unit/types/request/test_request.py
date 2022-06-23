import copy

import pytest
from docarray import Document, DocumentArray
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina.excepts import BadRequestType
from jina.helper import random_identity
from jina.proto import jina_pb2
from jina.proto.serializer import DataRequestProto
from jina.types.request.data import DataRequest, Response


@pytest.fixture(scope='function')
def req():
    r = jina_pb2.DataRequestProto()
    r.header.request_id = random_identity()
    r.data.docs.docs.add()
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
    assert not deserialized_request.is_decompressed_wo_data


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
    assert not deserialized_request.is_decompressed_wo_data


def test_status():
    r = DataRequest()
    r.docs.extend([Document()])
    r.add_exception(ValueError('intentional_error'))
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequestProto.FromString(byte_array)
    assert not deserialized_request.is_decompressed
    assert deserialized_request.status.code == jina_pb2.StatusProto.ERROR
    assert deserialized_request.is_decompressed_wo_data
    assert not deserialized_request.is_decompressed


def test_lazy_parameters():
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da

    parameters = {'a': 0}
    r.parameters = parameters
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequest(byte_array)
    assert not deserialized_request.is_decompressed
    assert deserialized_request.parameters == parameters
    assert deserialized_request.is_decompressed_wo_data
    assert not deserialized_request.is_decompressed

    with pytest.raises(AttributeError):
        deserialized_request._pb_body.data


def test_send_data_request_wo_data():
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da

    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequest(byte_array)

    assert deserialized_request.parameters is not None
    assert deserialized_request.is_decompressed_wo_data

    final_request = DataRequestProto.FromString(
        DataRequestProto.SerializeToString(deserialized_request)
    )

    assert len(final_request.docs) == doc_count
    assert final_request.docs == r.docs


def test_delete_of_pb2_wo_data():
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da

    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequest(byte_array)

    assert (
        deserialized_request.parameters is not None
    )  # access the parameters and create the proto wo data
    assert deserialized_request.is_decompressed_wo_data
    assert not deserialized_request.is_decompressed

    assert (
        deserialized_request.docs == r.docs
    )  # access docs, it should destroy the proto wo data

    assert (
        not deserialized_request.is_decompressed_wo_data
    )  # check that it is destroyed
    assert deserialized_request.is_decompressed
