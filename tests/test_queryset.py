import os

from jina.drivers.querylang.queryset.lookup import QuerySet, Q
from tests import JinaTestCase, random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):

    def test_docs_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(doc_id__lt=5, doc_id__gt=3)
        ssr = list(ss)
        self.assertEqual(len(ssr), 1)
        for d in ssr:
            self.assertTrue(3 < d.id < 5)

    def test_chunks_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(chunks__0__doc_id__exact=4)
        ssr = list(ss)
        self.assertEqual(len(ssr), 1)
        for d in ssr:
            self.assertTrue(3 < d.id < 5)
            self.assertEqual(len(d.chunks), 5)

    def test_nested_chunks_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(Q(chunks__filter=Q(doc_id__lt=5, doc_id__gt=3)))
        ssr = list(ss)
        self.assertEqual(len(ssr), 1)
        for d in ssr:
            self.assertTrue(3 < d.id < 5)
            self.assertEqual(len(d.chunks), 5)

    # def test_chunk_select_filter(self):
    #     s = random_docs(10)
    #     ss = QuerySet(s).filter(chunks__filter=Q(chunk_id=13))
    #     ssr = list(ss)
    #     self.assertEqual(len(ssr), 1)
    #     for d in ssr:
    #         print(d)
    #         for c in d.chunks:
    #             self.assertEqual(c.chunk_id, 10)
