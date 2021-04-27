import pytest
from google.protobuf.json_format import MessageToDict, MessageToJson

from jina.enums import RequestType
from jina.excepts import BadRequestType
from jina.helper import random_identity
from jina.proto import jina_pb2
from jina.types.request import Request
from jina.types.arrays.document import DocumentArray
from jina.types.arrays.querylang import QueryLangArray


@pytest.fixture(scope='function')
def req():
    r = jina_pb2.RequestProto()
    r.request_id = random_identity()
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


@pytest.mark.parametrize('req_type', ['index', 'search', 'train'])
def test_docs(req, req_type):
    request = Request(request=req, copy=False)
    request.request_type = req_type
    docs = request.docs
    assert request.is_used
    assert isinstance(docs, DocumentArray)
    if req_type == 'index':
        assert len(docs) == 1
    else:
        assert len(docs) == 0


@pytest.mark.parametrize('req_type', ['index', 'search', 'train'])
def test_groundtruth(req, req_type):
    request = Request(request=req, copy=False)
    request.request_type = req_type
    groundtruths = request.groundtruths
    assert request.is_used
    assert isinstance(groundtruths, DocumentArray)
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
    assert isinstance(queryset, QueryLangArray)


def test_command(req):
    request = Request(request=req, copy=False)
    request.request_type = 'control'
    cmd = request.command
    assert request.is_used
    assert cmd
    assert isinstance(cmd, str)


def test_as_pb_object(req):
    request = Request(request=req)
    request.proto
    assert request.is_used
    request = Request(request=None)
    assert request.proto
    assert request.is_used


def test_as_json_str(req):
    request = Request(request=req)
    assert isinstance(request.json(), str)
    request = Request(request=None)
    assert isinstance(request.json(), str)


def test_delete_request():
    req = Request()
    req.request_type = str(RequestType.DELETE)
    req.ids.extend(['123', '456'])
    assert req.dict()['delete']['ids'] == ['123', '456']
