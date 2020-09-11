import os
import numpy as np
from jina.drivers.querylang.queryset.lookup import QuerySet, Q
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.text = b'hello world'
        d.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
            c.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
            c.id = c_id
            c.parent_id = j
            c_id += 1
        yield d


cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_docs_filter():
    s = random_docs(10)
    ss = QuerySet(s).filter(id__lt=5, id__gt=3)
    ssr = list(ss)
    assert len(ssr) == 1
    for d in ssr:
        assert (3 < d.id < 5)


def test_docs_filter_equal():
    s = random_docs(10)
    ss = QuerySet(s).filter(id=4)
    ssr = list(ss)
    assert len(ssr) == 1
    for d in ssr:
        assert d.id == 4
        assert len(d.chunks) == 5


def test_nested_chunks_filter():
    s = random_docs(10)
    ss = QuerySet(s).filter(Q(chunks__filter=Q(id__lt=5, id__gt=3)))
    ssr = list(ss)
    assert len(ssr) == 1
    for d in ssr:
        assert len(d.chunks) == 5
