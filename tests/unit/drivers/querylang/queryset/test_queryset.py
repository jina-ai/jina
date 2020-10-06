import os

from jina.drivers.querylang.queryset.lookup import QuerySet, Q
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_docs_filter():
    s = random_docs(10)
    ss = QuerySet(s).filter(tags__id__lt=5, tags__id__gt=3)
    ssr = list(ss)
    assert len(ssr) == 1
    for d in ssr:
        assert (3 < d.tags['id'] < 5)


def test_docs_filter_equal():
    s = random_docs(10)
    ss = QuerySet(s).filter(tags__id=4)
    ssr = list(ss)
    assert len(ssr) == 1
    for d in ssr:
        assert int(d.tags['id']) == 4
        assert len(d.chunks) == 5


def test_nested_chunks_filter():
    s = random_docs(10)
    ss = QuerySet(s).filter(Q(chunks__filter=Q(tags__id__lt=35, tags__id__gt=33)))
    ssr = list(ss)
    assert len(ssr) == 1
    for d in ssr:
        assert len(d.chunks) == 5
