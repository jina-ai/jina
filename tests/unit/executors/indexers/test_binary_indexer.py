import copy

import numpy as np
import pytest

from jina.flow import Flow
from jina.proto import jina_pb2, uid
from jina.proto.ndarray.generic import GenericNdArray


@pytest.mark.parametrize('random_workspace_name', ['JINA_TEST_WORKSPACE_BINARY_PB'])
def test_binarypb_in_flow(test_metas):
    def random_docs(num_docs, chunks_per_doc=5, embed_dim=10, jitter=1):
        c_id = 3 * num_docs  # avoid collision with docs
        for j in range(num_docs):
            d = jina_pb2.Document()
            d.tags['id'] = j
            d.text = b'hello world'
            GenericNdArray(d.embedding).value = np.random.random([embed_dim + np.random.randint(0, jitter)])
            d.id = uid.new_doc_id(d)
            for k in range(chunks_per_doc):
                c = d.chunks.add()
                c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
                GenericNdArray(c.embedding).value = np.random.random([embed_dim + np.random.randint(0, jitter)])
                c.tags['id'] = c_id
                c.tags['parent_id'] = j
                c_id += 1
                c.parent_id = d.id
                c.id = uid.new_doc_id(c)
            yield d

    docs = list(random_docs(10))
    f = Flow(callback_on_body=True).add(uses='binarypb.yml')

    with f:
        f.index(docs, override_doc_id=False)

    def validate(req):
        assert len(docs) == len(req.docs)
        for d, d0 in zip(req.docs, docs):
            np.testing.assert_almost_equal(GenericNdArray(d.embedding).value,
                                           GenericNdArray(d0.embedding).value)

    docs_no_embedding = copy.deepcopy(docs)
    for d in docs_no_embedding:
        d.ClearField('embedding')
    with f:
        f.search(docs_no_embedding, output_fn=validate, override_doc_id=False)
