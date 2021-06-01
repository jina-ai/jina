import os

import numpy as np
import pytest

from jina import Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_uri_to_blob():
    doc = Document(uri=os.path.join(cur_dir, 'test.png'))
    doc.convert_image_uri_to_blob()
    assert isinstance(doc.blob, np.ndarray)
    assert doc.mime_type == 'image/png'
    assert doc.blob.shape == (85, 152, 3)  # h,w,c


def test_datauri_to_blob():
    doc = Document(uri=os.path.join(cur_dir, 'test.png'))
    doc.convert_uri_to_datauri()
    doc.convert_image_datauri_to_blob()
    assert isinstance(doc.blob, np.ndarray)
    assert doc.mime_type == 'image/png'
    assert doc.blob.shape == (85, 152, 3)  # h,w,c


def test_buffer_to_blob():
    doc = Document(uri=os.path.join(cur_dir, 'test.png'))
    doc.convert_uri_to_buffer()
    doc.convert_image_buffer_to_blob()
    assert isinstance(doc.blob, np.ndarray)
    assert doc.mime_type == 'image/png'
    assert doc.blob.shape == (85, 152, 3)  # h,w,c


def test_convert_buffer_to_blob():
    rand_state = np.random.RandomState(0)
    array = rand_state.random([10, 10])
    doc = Document(content=array.tobytes())
    assert doc.content_type == 'buffer'
    assert doc.mime_type == 'application/octet-stream'
    intialiazed_buffer = doc.buffer

    doc.convert_buffer_to_blob()
    assert doc.content_type == 'blob'
    converted_buffer_in_one_of = doc.buffer
    assert intialiazed_buffer != converted_buffer_in_one_of
    np.testing.assert_almost_equal(doc.content.reshape([10, 10]), array)


@pytest.mark.parametrize(
    'arr_size,mode', [(32 * 28, 'L'), ([32, 28], 'L'), ([32, 28, 3], 'RGB')]
)
def test_convert_blob_to_uri(arr_size, mode):
    doc = Document(content=np.random.randint(0, 255, arr_size))
    assert doc.blob.any()
    assert not doc.uri
    doc.convert_image_blob_to_uri(32, 28)
    assert doc.uri.startswith('data:image/png;base64,')
    assert doc.mime_type == 'image/png'


@pytest.mark.parametrize(
    'uri, mimetype',
    [
        (__file__, 'text/x-python'),
        ('http://google.com/index.html', 'text/html'),
        ('https://google.com/index.html', 'text/html'),
    ],
)
def test_convert_uri_to_buffer(uri, mimetype):
    d = Document(uri=uri)
    assert not d.buffer
    d.convert_uri_to_buffer()
    assert d.buffer
    assert d.mime_type == mimetype


@pytest.mark.parametrize(
    'converter', ['convert_buffer_to_uri', 'convert_content_to_uri']
)
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


@pytest.mark.parametrize(
    'uri, mimetype',
    [
        (__file__, 'text/x-python'),
        ('http://google.com/index.html', 'text/html'),
        ('https://google.com/index.html', 'text/html'),
    ],
)
def test_convert_uri_to_text(uri, mimetype):
    doc = Document(uri=uri, mime_type=mimetype)
    doc.convert_uri_to_text()
    if mimetype == 'text/html':
        assert '<!doctype html>' in doc.text
    elif mimetype == 'text/x-python':
        text_from_file = open(__file__).read()
        assert doc.text == text_from_file


def test_convert_text_to_uri_and_back():
    text_from_file = open(__file__).read()
    doc = Document(content=text_from_file, mime_type='text/x-python')
    assert doc.text
    assert doc.mime_type == 'text/x-python'
    doc.convert_text_to_uri()
    doc.convert_uri_to_text()
    assert doc.mime_type == 'text/plain'
    assert doc.text == text_from_file


def test_convert_content_to_uri():
    d = Document(content=np.random.random([10, 10]))
    with pytest.raises(NotImplementedError):
        d.convert_content_to_uri()


@pytest.mark.parametrize(
    'uri, mimetype',
    [
        (__file__, 'text/x-python'),
        ('http://google.com/index.html', 'text/html'),
        ('https://google.com/index.html', 'text/html'),
    ],
)
def test_convert_uri_to_data_uri(uri, mimetype):
    doc = Document(uri=uri, mime_type=mimetype)
    doc.convert_uri_to_datauri()
    assert doc.uri.startswith(f'data:{mimetype}')
    assert doc.mime_type == mimetype
