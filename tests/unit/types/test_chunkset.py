import pytest
from jina import Request

from jina.types.document import Document
from jina.types.sets.chunk_set import ChunkSet


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
    req = Request()
    req.request_type = 'index'
    req.docs.extend([
        document_factory.create(1, 'test 1'),
        document_factory.create(2, 'test 1'),
        document_factory.create(3, 'test 3')
    ])
    return req.as_pb_object.index.docs


@pytest.fixture
def chunkset(chunks, reference_doc):
    return ChunkSet(docs_proto=chunks, reference_doc=reference_doc)


def test_append_from_documents(chunkset, document_factory, reference_doc):
    chunk = document_factory.create(4, 'test 4')
    rv = chunkset.append(chunk)
    assert len(chunkset) == 4
    assert chunkset[-1].text == 'test 4'
    assert rv.text == chunk.text
    assert rv.parent_id == reference_doc.id
    assert rv.granularity == reference_doc.granularity + 1
    assert rv.mime_type == 'text/plain'
