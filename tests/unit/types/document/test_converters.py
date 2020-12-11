import numpy as np
import pytest

from jina import Document


def test_convert_buffer_to_blob():
    rand_state = np.random.RandomState(0)
    array = rand_state.random([10,10])
    doc = Document(content=array.tobytes())
    assert doc.content_type == 'buffer'
    intialiazed_buffer = doc.buffer

    doc.convert_buffer_to_blob()
    assert doc.content_type == 'blob'
    converted_buffer_in_one_of = doc.buffer
    assert intialiazed_buffer != converted_buffer_in_one_of
    np.testing.assert_almost_equal(doc.content.reshape([10, 10]), array)


@pytest.mark.parametrize('arr_size,mode', [(32 * 28, 'L'),
                                           ([32, 28], 'L'),
                                           ([32, 28, 3], 'RGB')])
def test_convert_blob_to_uri(arr_size, mode):
    doc = Document(content=np.random.randint(0, 255, arr_size))
    assert doc.blob.any()
    assert not doc.uri
    doc.convert_blob_to_uri(32, 28)
    assert doc.uri.startswith('data:image/png;base64,')


@pytest.mark.parametrize('uri, mimetype', [(__file__, 'text/x-python'),
                                           ('http://google.com/index.html', 'text/html'),
                                           ('https://google.com/index.html', 'text/html')])
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


@pytest.mark.parametrize('uri, mimetype', [(__file__, 'text/x-python'),
                                           ('http://google.com/index.html', 'text/html'),
                                           ('https://google.com/index.html', 'text/html')])
def test_convert_uri_to_text(uri, mimetype):
    doc = Document(uri=uri, mime_type=mimetype)
    intialiazed_buffer = doc.buffer 
    doc.convert_uri_to_text()
    converted_buffer = doc.buffer
    if mimetype == 'text/html': 
        assert '<!doctype html>' in doc.text
    elif mimetype == 'text/x-python':
        text_from_file = open(__file__).read()
        assert doc.text == text_from_file


def test_convert_text_to_uri_and_back():
    text_from_file = open(__file__).read()
    doc = Document(content=text_from_file, mime_type='text/x-python')
    assert doc.text
    doc.convert_text_to_uri()
    doc.convert_uri_to_text()
    assert doc.text == text_from_file


def test_convert_content_to_uri():
    d = Document(content=np.random.random([10, 10]))
    with pytest.raises(NotImplementedError):
        d.convert_content_to_uri()


@pytest.mark.parametrize('uri, mimetype', [(__file__, 'text/x-python'),
                                           ('http://google.com/index.html', 'text/html'),
                                           ('https://google.com/index.html', 'text/html')])
def test_convert_uri_to_data_uri(uri, mimetype):
    doc = Document(uri=uri, mime_type=mimetype)
    intialiazed_buffer = doc.buffer 
    intialiazed_uri = doc.uri
    doc.convert_uri_to_data_uri()
    converted_buffer = doc.buffer 
    converted_uri =  doc.uri
    print(doc.content_type)
    assert doc.uri.startswith(f'data:{mimetype}')
    assert intialiazed_uri != converted_uri
    assert converted_buffer != intialiazed_buffer
    assert doc.mime_type == mimetype
