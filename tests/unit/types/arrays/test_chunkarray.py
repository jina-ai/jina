import pytest

from jina.types.arrays.chunk import ChunkArray
from jina.types.document import Document
from jina.types.request import Request


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, idx, text, mime_type=None):
            with Document() as d:
                d.tags['id'] = idx
                d.text = text
                d.mime_type = mime_type
            return d

    return DocumentFactory()


@pytest.fixture
def reference_doc(document_factory):
    return document_factory.create(0, 'test ref', 'text/plain')


@pytest.fixture
def chunks(document_factory):
    req = Request().as_typed_request('data')
    req.docs.extend(
        [
            document_factory.create(1, 'test 1'),
            document_factory.create(2, 'test 1'),
            document_factory.create(3, 'test 3'),
        ]
    )
    return req.proto.data.docs


@pytest.fixture
def chunkarray(chunks, reference_doc):
    return ChunkArray(doc_views=chunks, reference_doc=reference_doc)


def test_append_from_documents(chunkarray, document_factory, reference_doc):
    chunk = document_factory.create(4, 'test 4')
    rv = chunkarray.append(chunk)
    assert len(chunkarray) == 4
    assert chunkarray[-1].text == 'test 4'
    assert rv.text == chunk.text
    assert rv.parent_id == reference_doc.id
    assert rv.granularity == reference_doc.granularity + 1
    assert rv.mime_type == 'text/plain'


def test_doc_chunks_init():
    d = Document(chunks=[Document()], matches=[Document()])
    assert d.chunks[0].granularity == 1
    assert d.chunks[0].adjacency == 0
    assert d.matches[0].adjacency == 1
    assert d.matches[0].granularity == 0
