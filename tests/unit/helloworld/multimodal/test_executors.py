import os

import pytest
from PIL import Image

from jina import Document, DocumentArray, Flow
from jina.helloworld.multimodal.my_executors import (
    Segmenter,
    TextEncoder,
    ImageCrafter,
    ImageEncoder,
)


@pytest.fixture(scope='function')
def segmenter_doc_array():
    inputs = [
        Document(tags={'caption': 'hello', 'image': '1.png'}),
        Document(tags={'caption': 'world', 'image': '2.png'}),
    ]
    return DocumentArray(inputs)


@pytest.fixture(scope='function')
def encoder_doc_array():
    document = Document()
    chunk_text = Document(text='hello', mime_type='text/plain')
    chunk_uri = Document(
        uri=f'{os.environ["HW_WORKDIR"]}/people-img/1.png', mime_type='image/jpeg'
    )
    document.chunks = [chunk_text, chunk_uri]
    return DocumentArray([document])


@pytest.fixture(scope='function')
def encoder_doc_array_for_search(encoder_doc_array, tmpdir):
    create_test_img(path=str(tmpdir), file_name='1.png')
    da = DocumentArray()
    for doc in encoder_doc_array:
        for chunk in doc.chunks:
            if chunk.mime_type == 'image/jpeg':
                chunk.convert_uri_to_datauri()
        da.append(doc)
    return da


def create_test_img(path, file_name):
    img_path = path + '/people-img/'
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    image = Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
    image.save(img_path + file_name, 'png')


def test_segmenter(segmenter_doc_array, tmpdir):
    """In this test, the ``DocumentArray`` has 2 ``Document`` with tags.
    Each ``Document`` will add 2 chunks based on tags, i.e. the text chunk
    and image uri chunk. Finally, we convert the uri of each ``Document``
    into datauri to show the image in front-end.
    """

    def validate(resp):
        assert len(resp.data.docs) == 2
        for doc in resp.data.docs:
            assert len(doc.chunks) == 2
            assert doc.chunks[0].mime_type == 'text/plain'
            assert doc.chunks[1].mime_type == 'image/jpeg'
            assert doc.uri.startswith('data')

    create_test_img(path=str(tmpdir), file_name='1.png')
    create_test_img(path=str(tmpdir), file_name='2.png')
    with Flow().add(uses=Segmenter) as f:
        f.index(inputs=segmenter_doc_array, on_done=validate)


def test_text_encoder(encoder_doc_array, tmpdir):
    """In this test, we input one ``DocumentArray`` with one ``Document``,
    and the `encode` method in the ``TextEncoder`` returns chunks.
    In the ``TextEncoder``, we filtered out all the modalities and only kept `text/plain`.
    So the 2 chunks should left only 1 chunk with modality of `text/plain`.
    And the embedding value of the ``Document`` is not empty once we finished encoding.
    """

    def validate(resp):
        assert len(resp.data.docs) == 1
        chunk = resp.data.docs[0]
        assert chunk.mime_type == 'text/plain'
        assert chunk.embedding

    create_test_img(path=str(tmpdir), file_name='1.png')
    with Flow().add(uses=TextEncoder) as f:
        f.index(inputs=encoder_doc_array, on_done=validate)


def test_image_crafter_index(encoder_doc_array, tmpdir):
    """In this test, we input one ``DocumentArray`` with one ``Document``,
    and the `craft` method in the ``ImageCrafter`` returns chunks.
    In the ``ImageCrafter``, we filtered out all the modalities and only kept `image/jpeg`.
    So the 2 chunks should left only 1 chunk.
    And the blob value of the ``Document`` is not empty once we finished crafting since
    we converted image uri/datauri to blob.
    """

    def validate(resp):
        assert len(resp.data.docs) == 1
        chunk = resp.data.docs[0]
        assert chunk.mime_type == 'image/jpeg'
        assert chunk.blob
        assert chunk.uri == ''

    create_test_img(path=str(tmpdir), file_name='1.png')
    with Flow().add(uses=ImageCrafter) as f:
        f.index(inputs=encoder_doc_array, on_done=validate)


def test_image_crafter_search(encoder_doc_array_for_search, tmpdir):
    def validate(resp):
        assert len(resp.data.docs) == 1
        chunk = resp.data.docs[0]
        assert chunk.mime_type == 'image/jpeg'
        assert chunk.blob
        assert chunk.uri == ''

    with Flow().add(uses=ImageCrafter) as f:
        f.search(inputs=encoder_doc_array_for_search, on_done=validate)


def test_image_encoder_index(encoder_doc_array, tmpdir):
    """In this test, we input one ``DocumentArray`` with one ``Document``,
    and the `encode` method in the ``ImageEncoder``.
    """

    def validate(resp):
        assert len(resp.data.docs) == 1
        for doc in resp.data.docs:
            assert doc.mime_type == 'image/jpeg'
            assert doc.embedding
            assert doc.embedding.dense.shape[0] == 1280

    create_test_img(path=str(tmpdir), file_name='1.png')
    with Flow().add(uses=ImageCrafter).add(uses=ImageEncoder) as f:
        f.index(inputs=encoder_doc_array, on_done=validate)


def test_image_encoder_search(encoder_doc_array_for_search, tmpdir):
    """In this test, we input one ``DocumentArray`` with one ``Document``,
    and the `encode` method in the ``ImageEncoder``.
    """

    def validate(resp):
        assert len(resp.data.docs) == 1
        for doc in resp.data.docs:
            assert doc.mime_type == 'image/jpeg'
            assert doc.embedding
            assert doc.embedding.dense.shape[0] == 1280

    with Flow().add(uses=ImageCrafter).add(uses=ImageEncoder) as f:
        f.search(inputs=encoder_doc_array_for_search, on_done=validate)
