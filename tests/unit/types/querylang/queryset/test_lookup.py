import pytest

from jina.types.querylang.queryset.lookup import LookupNode, LookupLeaf, Q, QuerySet
from jina.types.document import Document
from tests import random_docs


class MockId:
    def __init__(self, identity):
        self.id = identity


class MockStr:
    def __init__(self, string):
        self.str = string


class MockIter:
    def __init__(self, iterable):
        self.iter = iterable


@pytest.fixture(scope='function')
def docs():
    return random_docs(num_docs=10)


def test_lookup_leaf_exact():
    leaf = LookupLeaf(id__exact=1)
    mock1 = MockId(1)
    assert leaf.evaluate(mock1)
    mock2 = MockId(2)
    assert not leaf.evaluate(mock2)


def test_lookup_leaf_exact_document_tags():
    with Document() as doc:
        doc.tags['label'] = 'jina'
        leaf = LookupLeaf(tags__label='jina')
        assert leaf.evaluate(doc)
        leaf = LookupLeaf(tags__label='not_jina')
        assert not leaf.evaluate(doc)


def test_lookup_leaf_exact_document_tags_complex():
    with Document() as doc:
        doc.tags['key1'] = {'key2': 'jina'}
        leaf = LookupLeaf(tags__key1__key2='jina')
        assert leaf.evaluate(doc)
        leaf = LookupLeaf(tags__key1__key2='not_jina')
        assert not leaf.evaluate(doc)


def test_lookup_leaf_neq():
    leaf = LookupLeaf(id__neq=1)
    mock1 = MockId(1)
    assert not leaf.evaluate(mock1)
    mock2 = MockId(2)
    assert leaf.evaluate(mock2)


def test_lookup_leaf_gt():
    leaf = LookupLeaf(id__gt=1)
    mock0 = MockId(0)
    assert not leaf.evaluate(mock0)
    mock1 = MockId(1)
    assert not leaf.evaluate(mock1)
    mock2 = MockId(2)
    assert leaf.evaluate(mock2)


def test_lookup_leaf_gte():
    leaf = LookupLeaf(id__gte=1)
    mock0 = MockId(0)
    assert not leaf.evaluate(mock0)
    mock1 = MockId(1)
    assert leaf.evaluate(mock1)
    mock2 = MockId(2)
    assert leaf.evaluate(mock2)


def test_lookup_leaf_lt():
    leaf = LookupLeaf(id__lt=1)
    mock0 = MockId(0)
    assert leaf.evaluate(mock0)
    mock1 = MockId(1)
    assert not leaf.evaluate(mock1)
    mock2 = MockId(2)
    assert not leaf.evaluate(mock2)


def test_lookup_leaf_lte():
    leaf = LookupLeaf(id__lte=1)
    mock0 = MockId(0)
    assert leaf.evaluate(mock0)
    mock1 = MockId(1)
    assert leaf.evaluate(mock1)
    mock2 = MockId(2)
    assert not leaf.evaluate(mock2)


def test_lookup_leaf_contains():
    leaf = LookupLeaf(str__contains='jina')
    mock0 = MockStr('hey jina how are you')
    assert leaf.evaluate(mock0)
    mock1 = MockStr('not here')
    assert not leaf.evaluate(mock1)
    mock2 = MockStr('hey jInA how are you')
    assert not leaf.evaluate(mock2)


def test_lookup_leaf_icontains():
    leaf = LookupLeaf(str__icontains='jina')
    mock0 = MockStr('hey jInA how are you')
    assert leaf.evaluate(mock0)
    mock1 = MockStr('not here')
    assert not leaf.evaluate(mock1)


def test_lookup_leaf_startswith():
    leaf = LookupLeaf(str__startswith='jina')
    mock0 = MockStr('jina is the neural search solution')
    assert leaf.evaluate(mock0)
    mock1 = MockStr('hey, jina is the neural search solution')
    assert not leaf.evaluate(mock1)
    mock2 = MockStr('JiNa is the neural search solution')
    assert not leaf.evaluate(mock2)


def test_lookup_leaf_istartswith():
    leaf = LookupLeaf(str__istartswith='jina')
    mock0 = MockStr('jina is the neural search solution')
    assert leaf.evaluate(mock0)
    mock1 = MockStr('hey, jina is the neural search solution')
    assert not leaf.evaluate(mock1)
    mock2 = MockStr('JiNa is the neural search solution')
    assert leaf.evaluate(mock2)


def test_lookup_leaf_endswith():
    leaf = LookupLeaf(str__endswith='jina')
    mock0 = MockStr('how is jina')
    assert leaf.evaluate(mock0)
    mock1 = MockStr('hey, jina is the neural search solution')
    assert not leaf.evaluate(mock1)
    mock2 = MockStr('how is JiNa')
    assert not leaf.evaluate(mock2)


def test_lookup_leaf_iendswith():
    leaf = LookupLeaf(str__iendswith='jina')
    mock0 = MockStr('how is jina')
    assert leaf.evaluate(mock0)
    mock1 = MockStr('hey, jina is the neural search solution')
    assert not leaf.evaluate(mock1)
    mock2 = MockStr('how is JiNa')
    assert leaf.evaluate(mock2)


def test_lookup_leaf_regex():
    leaf = LookupLeaf(str__regex='j*na')
    mock0 = MockStr('hey, juna is good')
    assert leaf.evaluate(mock0)
    mock1 = MockStr('hey, Oinja is the neural search solution')
    assert not leaf.evaluate(mock1)
    mock2 = MockStr('how is JiNa')
    assert not leaf.evaluate(mock2)


def test_lookup_leaf_in():
    leaf = LookupLeaf(id__in=[0, 1, 2, 3])
    mock0 = MockId(3)
    assert leaf.evaluate(mock0)
    mock1 = MockId(4)
    assert not leaf.evaluate(mock1)


def test_lookup_leaf_None():
    leaf = LookupLeaf(id=3)
    mock0 = MockId(3)
    assert leaf.evaluate(mock0)
    mock1 = MockId(4)
    assert not leaf.evaluate(mock1)


def test_docs_filter(docs):
    filtered_docs = QuerySet(docs).filter(tags__id__lt=5, tags__id__gt=3)
    filtered_docs = list(filtered_docs)
    assert len(filtered_docs) == 1
    for d in filtered_docs:
        assert 3 < d.tags['id'] < 5


def test_docs_filter_equal(docs):
    filtered_docs = QuerySet(docs).filter(tags__id=4)
    filtered_docs = list(filtered_docs)
    assert len(filtered_docs) == 1
    for d in filtered_docs:
        assert int(d.tags['id']) == 4
        assert len(d.chunks) == 5


def test_nested_chunks_filter(docs):
    filtered_docs = QuerySet(docs).filter(
        Q(chunks__filter=Q(tags__id__lt=35, tags__id__gt=33))
    )
    filtered_docs = list(filtered_docs)
    assert len(filtered_docs) == 1
    for d in filtered_docs:
        assert len(d.chunks) == 5


def test_lookup_node_in():
    node = LookupNode()
    leaf1 = LookupLeaf(id__in=[0, 1])
    leaf2 = LookupLeaf(id__in=[1, 2])
    node.add_child(leaf1)
    node.add_child(leaf2)
    assert len(node.children) == 2

    mock0 = MockId(0)
    mock1 = MockId(1)
    mock2 = MockId(2)
    assert node.op == 'and'
    assert not node.evaluate(mock0)
    assert node.evaluate(mock1)
    assert not node.evaluate(mock2)

    assert not node.negate
    assert (~node).evaluate(mock0)
    assert not (~node).evaluate(mock1)
    assert (~node).evaluate(mock2)

    node.op = 'or'
    assert node.op == 'or'
    assert node.evaluate(mock0)
    assert node.evaluate(mock1)
    assert node.evaluate(mock2)

    assert (~node).negate
    assert (~node).evaluate(mock0)
    assert not (~node).evaluate(mock1)
    assert (~node).evaluate(mock2)
