import pytest

from docarray.array.chunk import ChunkArray
from docarray import Document
from docarray.proto.docarray_pb2 import DocumentArrayProto


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, idx, text, mime_type=None):
            d = Document(tags={'id': idx}, text=text, mime_type=mime_type)
            return d

    return DocumentFactory()


@pytest.fixture
def reference_doc(document_factory):
    return document_factory.create(0, 'test ref', 'text/plain')


@pytest.fixture
def chunks(document_factory):
    req = DocumentArrayProto()
    req.docs.extend(
        [
            document_factory.create(1, 'test 1').proto,
            document_factory.create(2, 'test 1').proto,
            document_factory.create(3, 'test 3').proto,
        ]
    )
    return req.docs


@pytest.fixture
def chunkarray(chunks, reference_doc):
    return ChunkArray(doc_views=chunks, reference_doc=reference_doc)


def test_append_from_documents(chunkarray, document_factory, reference_doc):
    chunk = document_factory.create(4, 'test 4')
    chunkarray.append(chunk)
    rv = chunkarray[-1]
    assert len(chunkarray) == 4
    assert chunkarray[-1].text == 'test 4'
    assert rv.text == chunk.text
    assert rv.parent_id == reference_doc.id
    assert rv.granularity == reference_doc.granularity + 1

    # match array is not neccessaily the same MIME type, think about multimodal
    assert rv.mime_type == ''


def test_doc_chunks_init():
    d = Document(chunks=[Document()], matches=[Document()])
    assert d.chunks[0].granularity == 1
    assert d.chunks[0].adjacency == 0
    assert d.matches[0].adjacency == 1
    assert d.matches[0].granularity == 0
