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
    assert not deserialized_request.is_decompressed_with_data
    assert len(deserialized_request.docs) == doc_count
    assert deserialized_request.docs == r.docs
    assert deserialized_request.is_decompressed_with_data
    assert not deserialized_request.is_decompressed_wo_data


def test_lazy_serialization_bytes(request_proto_bytes):
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs_bytes = da.to_bytes()
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequestProto.FromString(byte_array)
    assert not deserialized_request.is_decompressed_with_data
    assert len(deserialized_request.docs) == doc_count
    assert deserialized_request.docs == r.docs
    assert deserialized_request.is_decompressed_with_data
    assert not deserialized_request.is_decompressed_wo_data


def test_status():
    r = DataRequest()
    r.docs.extend([Document()])
    r.add_exception(ValueError('intentional_error'))
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequestProto.FromString(byte_array)
    assert not deserialized_request.is_decompressed_with_data
    assert deserialized_request.status.code == jina_pb2.StatusProto.ERROR
    assert deserialized_request.is_decompressed_wo_data
    assert not deserialized_request.is_decompressed_with_data


def test_load_parameters_wo_loading_data():  # test that accessing parameters does not load the data
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da

    parameters = {'a': 0}
    r.parameters = parameters
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequest(byte_array)
    assert not deserialized_request.is_decompressed_with_data
    assert deserialized_request.parameters == parameters
    assert deserialized_request.is_decompressed_wo_data
    assert not deserialized_request.is_decompressed_with_data


def test_change_parameters_wo_loading_data():  # test that changing parameters does not load the data
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da

    parameters = {'a': 0}
    new_parameters = {'b': 1}

    r.parameters = parameters
    byte_array = DataRequestProto.SerializeToString(r)

    deserialized_request = DataRequest(byte_array)
    assert not deserialized_request.is_decompressed_with_data
    assert deserialized_request.parameters == parameters
    assert deserialized_request.is_decompressed_wo_data

    deserialized_request.parameters = new_parameters

    new_byte_array = DataRequestProto.SerializeToString(deserialized_request)
    new_deserialized_request = DataRequest(new_byte_array)

    assert new_deserialized_request.parameters == new_parameters
    new_deserialized_request.docs
    assert new_deserialized_request.docs == da


def test_send_data_request_wo_data():  # check that when sending a DataRequestWoData the docs are sent
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


def test_delete_of_pb2_wo_data():  # ensure that pb2_wo_data is destroyed when accessing data
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
    assert not deserialized_request.is_decompressed_with_data

    assert (
        deserialized_request.docs == r.docs
    )  # access docs, it should destroy the proto wo data

    assert (
        not deserialized_request.is_decompressed_wo_data
    )  # check that it is destroyed
    assert deserialized_request.is_decompressed_with_data


def test_change_only_params():  # check that when sending a DataRequestWoData the docs are sent
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


def test_proto_wo_data_to_data(request_proto_bytes):
    proto_wo_data = jina_pb2.DataRequestProtoWoData()
    proto_wo_data.ParseFromString(request_proto_bytes)

    proto_data = jina_pb2.DataRequestProto()
    proto_data.ParseFromString(request_proto_bytes)

    assert (  # check that once we serialize both proto have the same content
        proto_wo_data.SerializePartialToString()
        == proto_data.SerializePartialToString()
    )


@pytest.fixture()
def request_proto_bytes():
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da
    return DataRequestProto.SerializeToString(r)


def test_proto_wo_data_to_param_change_data(request_proto_bytes):

    proto_wo_data = jina_pb2.DataRequestProtoWoData()
    proto_wo_data.ParseFromString(request_proto_bytes)

    proto_data = jina_pb2.DataRequestProto()
    proto_data.ParseFromString(request_proto_bytes)

    for proto in [proto_data, proto_wo_data]:
        proto.parameters.Clear()
        proto.parameters.update({'b': 1})

    assert (  # check that once we serialize both proto have the same content
        proto_wo_data.SerializePartialToString()
        == proto_data.SerializePartialToString()
    )


def test_proto_wo_data_docs():  # check if we can access the docs after deserializing from a proto_wo_data
    doc_count = 1000
    r = DataRequest()
    da = r.docs
    da.extend([Document(text='534534534er5yr5y645745675675675345')] * doc_count)
    r.data.docs = da

    proto_wo_data = jina_pb2.DataRequestProtoWoData()
    proto_wo_data.ParseFromString(DataRequestProto.SerializeToString(r))

    bytes_ = proto_wo_data.SerializePartialToString()

    new_data_request = DataRequest(bytes_)

    assert new_data_request.docs == r.docs


def test_req_add_get_executors():
    r = DataRequest()
    r.add_executor('one')
    assert r.last_executor == 'one'
    r.add_executor('two')
    assert r.last_executor == 'two'

    r2 = DataRequest.from_proto(r.proto)
    assert r2.last_executor == 'two'
