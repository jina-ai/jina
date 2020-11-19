import numpy as np
import pytest

from jina import Document


def test_convert_buffer_to_blob():
    c = np.random.random([10, 10])
    d = Document(content=c.tobytes())

    assert d.content_type == 'buffer'
    d.convert_buffer_to_blob()
    assert d.content_type == 'blob'
    np.testing.assert_almost_equal(d.content.reshape([10, 10]), c)


@pytest.mark.parametrize('arr_size,mode', [(32 * 28, 'L'),
                                           ([32, 28], 'L'),
                                           ([32, 28, 3], 'RGB')])
def test_convert_blob_to_uri(arr_size, mode):
    d = Document(content=np.random.randint(0, 255, arr_size))
    assert not d.uri
    d.convert_blob_to_uri(32, 28)
    assert d.uri.startswith('data:image/png;base64,')


@pytest.mark.parametrize('uri, mimetype', [(__file__, 'text/x-python'),
                                           ('https://api.jina.ai/latest.json', 'text/plain')])
def test_convert_uri_to_buffer(uri, mimetype):
    d = Document(uri=uri)
    assert not d.buffer
    d.convert_uri_to_buffer()
    assert d.buffer
    assert d.mime_type == mimetype


@pytest.mark.parametrize('converter', ['convert_buffer_to_uri', 'convert_content_to_uri'])
def test_convert_buffer_to_uri(converter):
    d = Document(content=open(__file__).read().encode(), mime_type='text/x-python')
    assert d.buffer
    getattr(d, converter)()
    assert d.uri.startswith('data:text/x-python;')


@pytest.mark.parametrize('converter', ['convert_text_to_uri', 'convert_content_to_uri'])
def test_convert_text_to_uri(converter):
    d = Document(content=open(__file__).read(), mime_type='text/x-python')
    assert d.text
    getattr(d, converter)()
    assert d.uri.startswith('data:text/x-python;')


def test_convert_uri_to_text():
    t = open(__file__).read()
    d = Document(content=t, mime_type='text/x-python')
    assert d.text
    d.convert_text_to_uri()
    d.text = ''
    assert not d.text
    d.convert_uri_to_text()
    assert d.text == t


def test_convert_content_to_uri():
    d = Document(content=np.random.random([10, 10]))
    with pytest.raises(NotImplementedError):
        d.convert_content_to_uri()
