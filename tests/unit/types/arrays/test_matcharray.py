import pytest

import numpy as np

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
    req = Request().as_typed_request('data')
    req.docs.extend(
        [
            document_factory.create(1, 'test 1'),
            document_factory.create(2, 'test 1'),
            document_factory.create(3, 'test 3'),
        ]
    )
    return req.docs


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


def test_matches_sort_by_document_interface_in_proto():
    docs = [Document(weight=(10 - i)) for i in range(10)]
    query = Document()
    query.matches = docs
    assert len(query.matches) == 10
    assert query.matches[0].weight == 10

    query.matches.sort(key=lambda m: m.weight)
    assert query.matches[0].weight == 1


def test_matches_sort_by_document_interface_not_in_proto():
    docs = [Document(embedding=np.array([1] * (10 - i))) for i in range(10)]
    query = Document()
    query.matches = docs
    assert len(query.matches) == 10
    assert query.matches[0].embedding.shape == (10,)

    query.matches.sort(key=lambda m: m.embedding.shape[0])
    assert query.matches[0].embedding.shape == (1,)


def test_query_match_array_sort_scores():
    query = Document()
    query.matches = [
        Document(id=i, copy=True, scores={'euclid': 10 - i}) for i in range(10)
    ]
    assert query.matches[0].id == '0'
    assert query.matches[0].scores['euclid'].value == 10
    query.matches.sort(
        key=lambda m: m.scores['euclid'].value
    )  # sort matches by their values
    assert query.matches[0].id == '9'
    assert query.matches[0].scores['euclid'].value == 1
