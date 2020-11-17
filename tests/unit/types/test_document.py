import numpy as np
import pytest
from google.protobuf.json_format import MessageToDict

from jina import NdArray
from jina.proto.jina_pb2 import DocumentProto
from jina.types.document import Document


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
    a.update(embedding=b, tags=c, location=d, modality=e)
    np.testing.assert_equal(a.embedding, b)
    assert list(a.location) == d
    assert a.modality == e
    assert MessageToDict(a.tags) == c


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
    with pytest.raises(ValueError):
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
