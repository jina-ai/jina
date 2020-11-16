import numpy as np
import pytest

from jina.proto.jina_pb2 import DocumentProto
from jina.types.document import Document


def test_ndarray_get_set():
    a = Document()
    b = np.random.random([10, 10])
    a.blob = b
    np.testing.assert_equal(a.blob, b)

    c = np.random.random([10, 10])
    a.embedding = c
    np.testing.assert_equal(a.embedding, c)


def test_uri_get_set():
    a = Document()
    a.uri = 'https://abc.com/a.jpg'
    assert a.uri == 'https://abc.com/a.jpg'
    assert a.mime_type == 'image/jpeg'

    with pytest.raises(ValueError):
        a.uri = 'abcdefg'


def test_no_copy_construct():
    a = DocumentProto()
    b = Document(a, copy=False)
    a.id = '123'
    assert b.id == '123'

    b.id = '456'
    assert b.id == '456'


def test_copy_construct():
    a = DocumentProto()
    b = Document(a, copy=True)
    a.id = '123'
    assert b.id != '123'

    b.id = '456'
    assert a.id == '123'


def test_id_context():
    with Document() as d:
        assert not d.id
        d.buffer = b'123'
    assert d.id
