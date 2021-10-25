import inspect
import os

import numpy as np
import pytest
from jina import Document, __windows__
from jina.types.document import ContentConversionMixin
from jina.types.document.generators import from_files

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_self_as_return():
    num_fn = 0
    for f in inspect.getmembers(ContentConversionMixin):
        if (
            callable(f[1])
            and not f[1].__name__.startswith('_')
            and not f[0].startswith('_')
            and not f[1].__name__.startswith('dump')
        ):
            assert inspect.getfullargspec(f[1]).annotations['return'] == 'Document'
            num_fn += 1
    assert num_fn


def test_image_convert_pipe(pytestconfig):
    for d in from_files(f'{pytestconfig.rootdir}/.github/**/*.png'):
        (
            d.convert_image_uri_to_blob()
            .convert_uri_to_datauri()
            .resize_image_blob(64, 64)
            .normalize_image_blob()
            .set_image_blob_channel_axis(-1, 0)
        )
        assert d.blob.shape == (3, 64, 64)
        assert d.uri


def test_uri_to_blob():
    doc = Document(uri=os.path.join(cur_dir, 'test.png'))
    doc.convert_image_uri_to_blob()
    assert isinstance(doc.blob, np.ndarray)
    assert doc.mime_type == 'image/png'
    assert doc.blob.shape == (85, 152, 3)  # h,w,c


def test_datauri_to_blob():
    doc = Document(uri=os.path.join(cur_dir, 'test.png'))
    doc.convert_uri_to_datauri()
    assert not doc.blob
    assert doc.mime_type == 'image/png'


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
    intialiazed_buffer = doc.buffer

    doc.convert_buffer_to_blob()
    assert doc.content_type == 'blob'
    converted_buffer_in_one_of = doc.buffer
    assert intialiazed_buffer != converted_buffer_in_one_of
    np.testing.assert_almost_equal(doc.content.reshape([10, 10]), array)


@pytest.mark.parametrize('shape, channel_axis', [((3, 32, 32), 0), ((32, 32, 3), -1)])
def test_image_normalize(shape, channel_axis):
    doc = Document(content=np.random.randint(0, 255, shape, dtype=np.uint8))
    doc.normalize_image_blob(channel_axis=channel_axis)
    assert doc.blob.ndim == 3
    assert doc.blob.shape == shape
    assert doc.blob.dtype == np.float32


@pytest.mark.parametrize(
    'arr_size, color_axis, height, width',
    [
        ((32 * 28), -1, None, None),  # single line
        ([32, 28], -1, None, None),  # without channel info
        ([32, 28, 3], -1, None, None),  # h, w, c (rgb)
        ([3, 32, 28], 0, None, None),  # c, h, w  (rgb)
        ([1, 32, 28], 0, None, None),  # c, h, w, (greyscale)
        ([32, 28, 1], -1, None, None),  # h, w, c, (greyscale)
        ((32 * 28), -1, 896, 1),  # single line
        ([32, 28], -1, 32, 28),  # without channel info
        ([32, 28, 3], -1, 32, 28),  # h, w, c (rgb)
        ([3, 32, 28], 0, 32, 28),  # c, h, w  (rgb)
        ([1, 32, 28], 0, 32, 28),  # c, h, w, (greyscale)
        ([32, 28, 1], -1, 32, 28),  # h, w, c, (greyscale)
    ],
)
def test_convert_image_blob_to_uri(arr_size, color_axis, width, height):
    doc = Document(content=np.random.randint(0, 255, arr_size))
    assert doc.blob.any()
    assert not doc.uri
    print(doc.blob.shape, color_axis)
    doc.resize_image_blob(channel_axis=color_axis, width=width, height=height)

    # doc.convert_image_blob_to_uri(
    # )
    # assert doc.uri.startswith('data:image/png;base64,')
    # assert doc.mime_type == 'image/png'


@pytest.mark.xfail(
    condition=__windows__, reason='x-python is not detected on windows CI'
)
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


@pytest.mark.xfail(
    condition=__windows__, reason='x-python is not detected on windows CI'
)
@pytest.mark.parametrize(
    'uri, mimetype',
    [
        pytest.param(
            __file__,
            'text/x-python',
            marks=pytest.mark.xfail(
                condition=__windows__, reason='x-python is not detected on windows CI'
            ),
        ),
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
