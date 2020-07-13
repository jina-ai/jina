import os

import numpy as np

from jina.drivers.helper import array2pb
from jina.drivers.querylang.queryset.lookup import QuerySet, Q
from jina.proto import jina_pb2
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.doc_id = j
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d


class MyTestCase(JinaTestCase):

    def test_docs_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(doc_id__lt=5, doc_id__gt=3)
        ssr = list(ss)
        self.assertEqual(len(ssr), 1)
        for d in ssr:
            self.assertTrue(3 < d.doc_id < 5)

    def test_chunks_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(chunks__0__doc_id__exact=4)
        ssr = list(ss)
        self.assertEqual(len(ssr), 1)
        for d in ssr:
            self.assertTrue(3 < d.doc_id < 5)
            self.assertEqual(len(d.chunks), 5)

    def test_nested_chunks_filter(self):
        s = random_docs(10)
        ss = QuerySet(s).filter(Q(chunks__filter=Q(doc_id__lt=5, doc_id__gt=3)))
        ssr = list(ss)
        self.assertEqual(len(ssr), 1)
        for d in ssr:
            self.assertTrue(3 < d.doc_id < 5)
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
