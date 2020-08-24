import os

from jina.drivers.querylang.queryset.lookup import QuerySet, Q
from tests import JinaTestCase, random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


class QuerySetTestCase(JinaTestCase):

    def test_docs_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(id__lt=5, id__gt=3)
        ssr = list(ss)
        assert len(ssr) == 1
        for d in ssr:
            self.assertTrue(3 < d.id < 5)

    def test_docs_filter_equal(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(id=4)
        ssr = list(ss)
        assert len(ssr) == 1
        for d in ssr:
            assert d.id == 4
            assert len(d.chunks) == 5

    def test_nested_chunks_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(Q(chunks__filter=Q(id__lt=5, id__gt=3)))
        ssr = list(ss)
        assert len(ssr) == 1
        for d in ssr:
            assert len(d.chunks) == 5
