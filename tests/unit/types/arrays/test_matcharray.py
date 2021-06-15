import pytest

from jina.types.arrays.match import MatchArray
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
def matches(document_factory):
    req = Request()
    req.request_type = 'data'
    req.docs.extend(
        [
            document_factory.create(1, 'test 1'),
            document_factory.create(2, 'test 1'),
            document_factory.create(3, 'test 3'),
        ]
    )
    return req.proto.data.docs


@pytest.fixture
def matcharray(matches, reference_doc):
    return MatchArray(doc_views=matches, reference_doc=reference_doc)


def test_append_from_documents(matcharray, document_factory, reference_doc):
    match = document_factory.create(4, 'test 4')
    match.scores['score'] = 10
    rv = matcharray.append(match)
    assert len(matcharray) == 4
    assert matcharray[-1].text == 'test 4'
    assert rv.text == match.text
    assert rv.granularity == reference_doc.granularity
    assert rv.adjacency == reference_doc.adjacency + 1
    assert rv.mime_type == 'text/plain'
    assert rv.scores['score'].ref_id == reference_doc.id


def test_mime_type_not_reassigned():
    d = Document()
    m = Document()
    assert m.mime_type == ''
    d.mime_type = 'text/plain'
    r = d.matches.append(m)
    assert r.mime_type == ''
