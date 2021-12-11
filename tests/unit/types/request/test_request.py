import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from docarray.proto.docarray_pb2 import DocumentProto
from jina.excepts import BadRequestType
from jina.helper import random_identity
from jina.proto import jina_pb2
from jina import DocumentArray, Document
from jina.types.request import Request, Response
from tests import random_docs


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


def test_request_docs_mutable_iterator():
    """To test the weak reference work in docs"""
    r = Request().as_typed_request('data')
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
    r = Request().as_typed_request('data')
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
