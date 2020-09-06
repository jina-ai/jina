import os
import shutil

import numpy as np

from jina.drivers.helper import array2pb
from jina.flow import Flow
from jina.proto import jina_pb2

cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_docs(num_docs):
    vecs = np.random.random([num_docs, 2])
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.embedding.CopyFrom(array2pb(vecs[j]))
        yield d


def test_high_order_matches():
    f = Flow(callback_on_body=True).add(uses=os.path.join(cur_dir, 'yaml/test-adjacency.yml'))

    with f:
        f.index(random_docs(100))

    with f:
        f.search(random_docs(1), output_fn=validate)

    shutil.rmtree('test-index-file', ignore_errors=False, onerror=None)


def validate(req):
    assert len(req.docs) == 1
    assert len(req.docs[0].matches) == 5
    assert len(req.docs[0].matches) == 5
    assert len(req.docs[0].matches[0].matches) == 5
    assert len(req.docs[0].matches[-1].matches) == 5
    assert len(req.docs[0].matches[0].matches[0].matches) == 0


test_high_order_matches()