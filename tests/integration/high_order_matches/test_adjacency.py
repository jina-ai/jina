import os
import shutil

import pytest

from jina.flow import Flow
from tests import random_docs, validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


# def test_high_order_matches():
#     f = Flow().add(uses=os.path.join(cur_dir, 'test-adjacency.yml'))
#
#     with f:
#         f.index(random_docs(100, chunks_per_doc=0, embed_dim=2))
#
#     with f:
#         f.search(random_docs(1, chunks_per_doc=0, embed_dim=2), on_done=validate)


@pytest.mark.parametrize('restful', [False, True])
def test_high_order_matches_integrated(mocker, restful):
    def validate(req):
        assert len(req.docs) == 1
        assert len(req.docs[0].matches) == 5
        assert len(req.docs[0].matches) == 5
        assert len(req.docs[0].matches[0].matches) == 5
        assert len(req.docs[0].matches[-1].matches) == 5
        assert len(req.docs[0].matches[0].matches[0].matches) == 0

    response_mock = mocker.Mock()
    # this is equivalent to the last test but with simplified YAML spec.
    f = Flow(restful=restful).add(uses=os.path.join(cur_dir, 'test-adjacency-integrated.yml'))

    with f:
        f.index(random_docs(100, chunks_per_doc=0, embed_dim=2))

    with f:
        f.search(random_docs(1, chunks_per_doc=0, embed_dim=2), on_done=response_mock)

    shutil.rmtree('test-index-file', ignore_errors=False, onerror=None)
    validate_callback(response_mock, validate)
