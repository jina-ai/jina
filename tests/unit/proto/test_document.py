import numpy as np
import pytest

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
