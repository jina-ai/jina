import copy
import os
import sys
import time

import numpy as np
import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from docarray.proto.docarray_pb2 import DocumentProto
from jina.excepts import BadRequestType
from jina.helper import random_identity
from jina.proto import jina_pb2
from jina import DocumentArray, Document
from jina.proto.serializer import DataRequestProtoOld, DataRequestProtoHac
from jina.proto.serializer import DataRequestProto
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest, Response
from jina.types.request.data_hack import DataRequestHac
from jina.types.request.data_old import DataRequestOld
from jina.types.request.data import DataRequest, Response
from tests import random_docs


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


def test_request_docs_mutable_iterator():
    """To test the weak reference work in docs"""
    r = DataRequest()
    for d in random_docs(10):
        r.docs.append(d)

    for idx, d in enumerate(r.docs):
        assert isinstance(d, Document)
        d.text = f'look I changed it! {idx}'

    # iterate it again should see the change
    doc_pointers = []
    for idx, d in enumerate(r.docs):
        assert isinstance(d, Document)
        assert d.text == f'look I changed it! {idx}'
        doc_pointers.append(d)

    # pb-lize it should see the change
    rpb = r.proto

    for idx, d in enumerate(rpb.data.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for idx, d in enumerate(rpb.data.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == 'now i change it back'


def test_request_docs_chunks_mutable_iterator():
    """Test if weak reference work in nested docs"""
    r = DataRequest()
    for d in random_docs(10):
        r.docs.append(d)

    for d in r.docs:
        assert isinstance(d, Document)
        for idx, c in enumerate(d.chunks):
            assert isinstance(d, Document)
            c.text = f'look I changed it! {idx}'

    # iterate it again should see the change
    doc_pointers = []
    for d in r.docs:
        assert isinstance(d, Document)
        for idx, c in enumerate(d.chunks):
            assert c.text == f'look I changed it! {idx}'
            doc_pointers.append(c)

    # pb-lize it should see the change
    rpb = r.proto

    for d in rpb.data.docs:
        assert isinstance(d, DocumentProto)
        for idx, c in enumerate(d.chunks):
            assert isinstance(c, DocumentProto)
            assert c.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for d in rpb.data.docs:
        assert isinstance(d, DocumentProto)
        for c in d.chunks:
            assert c.text == 'now i change it back'


@pytest.mark.parametrize(
    'cls',
    [
        (DataRequest, DataRequestProto),
        (DataRequestOld, DataRequestProtoOld),
        (DataRequestHac, DataRequestProtoHac),
    ],
)
def test_lazy_data_serialization(cls):
    req = cls[0]()
    req.docs.extend(
        DocumentArray([Document(embedding=np.random.rand(100, 100, 10))] * 1000)
    )
    bla = cls[1].SerializeToString(req)

    print('start measuring')
    start = time.time()
    deserialized_request = cls[1].FromString(bla)
    end = time.time() - start

    start_s = time.time()
    bla2 = cls[1].SerializeToString(deserialized_request)
    end_s = time.time() - start_s
    print('end measuring')

    print(
        f'{cls} serialized size {sys.getsizeof(bla)} serialized size {sys.getsizeof(bla2)} deserialization took {end*1000} ms serilization took {end_s*1000} ms'
    )

    print('do access docs')
    # assert not deserialized_request.is_decompressed
    # assert not deserialized_request._docs
    start_doc = time.time()
    assert len(deserialized_request.docs) == 1000
    end = time.time() - start_doc
    print(f'{cls} took {end*1000} ms')
    # assert deserialized_request._docs
    # assert deserialized_request.is_decompressed
