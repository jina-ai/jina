import os
import shutil

from jina.flow import Flow
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


# def test_high_order_matches():
#     f = Flow(callback_on='body').add(uses=os.path.join(cur_dir, 'test-adjacency.yml'))
#
#     with f:
#         f.index(random_docs(100, chunks_per_doc=0, embed_dim=2))
#
#     with f:
#         f.search(random_docs(1, chunks_per_doc=0, embed_dim=2), output_fn=validate)


def test_high_order_matches_integrated():
    # this is equivalent to the last test but with simplified YAML spec.
    f = Flow(callback_on='body').add(uses=os.path.join(cur_dir, 'test-adjacency-integrated.yml'))

    with f:
        f.index(random_docs(100, chunks_per_doc=0, embed_dim=2))

    with f:
        f.search(random_docs(1, chunks_per_doc=0, embed_dim=2), output_fn=validate)


def validate(req):
    shutil.rmtree('test-index-file', ignore_errors=False, onerror=None)
    assert len(req.docs) == 1
    assert len(req.docs[0].matches) == 5
    assert len(req.docs[0].matches) == 5
    assert len(req.docs[0].matches[0].matches) == 5
    assert len(req.docs[0].matches[-1].matches) == 5
    assert len(req.docs[0].matches[0].matches[0].matches) == 0
