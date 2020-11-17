import copy

import numpy as np
import pytest

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.document import uid
from jina.types.ndarray.generic import NdArray

from tests import random_docs


@pytest.mark.parametrize('random_workspace_name', ['JINA_TEST_WORKSPACE_BINARY_PB'])
def test_binarypb_in_flow(test_metas):
    docs = list(random_docs(10))
    f = Flow(callback_on='body').add(uses='binarypb.yml')

    with f:
        f.index(docs, override_doc_id=False)

    def validate(req):
        assert len(docs) == len(req.docs)
        for d, d0 in zip(req.docs, docs):
            np.testing.assert_almost_equal(NdArray(d.embedding).value,
                                           NdArray(d0.embedding).value)

    docs_no_embedding = copy.deepcopy(docs)
    for d in docs_no_embedding:
        d.ClearField('embedding')
    with f:
        f.search(docs_no_embedding, output_fn=validate, override_doc_id=False)
