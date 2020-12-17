import numpy as np
import pytest
from google.protobuf.json_format import MessageToDict

from jina import NdArray, Request
from jina.proto.jina_pb2 import DocumentProto
from jina.types.document import Document, BadDocID
from tests import random_docs

DOCUMENTS_PER_LEVEL = 1


@pytest.mark.parametrize('field', ['blob', 'embedding'])
def test_ndarray_get_set(field):
    a = Document()
    b = np.random.random([10, 10])
    setattr(a, field, b)
    np.testing.assert_equal(getattr(a, field), b)

    b = np.random.random([10, 10])
    c = NdArray()
    c.value = b
    setattr(a, field, c)
    np.testing.assert_equal(getattr(a, field), b)

    b = np.random.random([10, 10])
    c = NdArray()
    c.value = b
    setattr(a, field, c.proto)
    np.testing.assert_equal(getattr(a, field), b)


def test_doc_update_fields():
    a = Document()
    b = np.random.random([10, 10])
    c = {'tags': 'string', 'tag-tag': {'tags': 123.45}}
    d = [12, 34, 56]
    e = 'text-mod'
    w = 2.0
    a.set_attrs(embedding=b, tags=c, location=d, modality=e, weight=w)
    np.testing.assert_equal(a.embedding, b)
    assert list(a.location) == d
    assert a.modality == e
    assert MessageToDict(a.tags) == c
    assert a.weight == w


def test_granularity_get_set():
    d = Document()
    d.granularity = 1
    assert d.granularity == 1


def test_uri_get_set():
    a = Document()
    a.uri = 'https://abc.com/a.jpg'
    assert a.uri == 'https://abc.com/a.jpg'
    assert a.mime_type == 'image/jpeg'

    with pytest.raises(ValueError):
        a.uri = 'abcdefg'


def test_set_get_mime():
    a = Document()
    a.mime_type = 'jpg'
    assert a.mime_type == 'image/jpeg'
    b = Document()
    b.mime_type = 'jpeg'
    assert b.mime_type == 'image/jpeg'
    c = Document()
    c.mime_type = '.jpg'
    assert c.mime_type == 'image/jpeg'


def test_no_copy_construct():
    a = DocumentProto()
    b = Document(a, copy=False)
    a.id = '1' * 16
    assert b.id == '1' * 16

    b.id = '2' * 16
    assert a.id == '2' * 16


def test_copy_construct():
    a = DocumentProto()
    b = Document(a, copy=True)
    a.id = '1' * 16
    assert b.id != '1' * 16

    b.id = '2' * 16
    assert a.id == '1' * 16


def test_bad_good_doc_id():
    b = Document()
    with pytest.raises(BadDocID):
        b.id = 'hello'
    b.id = 'abcd' * 4
    b.id = 'de09' * 4
    b.id = 'af54' * 4
    b.id = 'abcdef0123456789'


def test_id_context():
    with Document() as d:
        assert not d.id
        d.buffer = b'123'
    assert d.id


def test_doc_content():
    d = Document()
    assert d.content is None
    d.text = 'abc'
    assert d.content == 'abc'
    c = np.random.random([10, 10])
    d.blob = c
    np.testing.assert_equal(d.content, c)
    d.buffer = b'123'
    assert d.buffer == b'123'


def test_request_docs_mutable_iterator():
    """To test the weak reference work in docs"""
    r = Request()
    r.request_type = 'index'
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
    rpb = r.as_pb_object

    for idx, d in enumerate(rpb.index.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for idx, d in enumerate(rpb.index.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == 'now i change it back'


def test_request_docs_chunks_mutable_iterator():
    """Test if weak reference work in nested docs"""
    r = Request()
    r.request_type = 'index'
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
    rpb = r.as_pb_object

    for d in rpb.index.docs:
        assert isinstance(d, DocumentProto)
        for idx, c in enumerate(d.chunks):
            assert isinstance(c, DocumentProto)
            assert c.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for d in rpb.index.docs:
        assert isinstance(d, DocumentProto)
        for c in d.chunks:
            assert c.text == 'now i change it back'


def test_doc_setattr():
    from jina import Document

    with Document() as root:
        root.text = 'abc'

    assert root.adjacency == 0

    with Document() as match:
        match.text = 'def'
        m = root.matches.append(match)

    with Document() as chunk:
        chunk.text = 'def'
        c = root.chunks.append(chunk)

    assert len(root.matches) == 1
    assert root.matches[0].granularity == 0
    assert root.matches[0].adjacency == 1

    assert m.granularity == 0
    assert m.adjacency == 1

    assert len(root.chunks) == 1
    assert root.chunks[0].granularity == 1
    assert root.chunks[0].adjacency == 0

    assert c.granularity == 1
    assert c.adjacency == 0
