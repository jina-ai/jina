import pytest
import numpy as np
from jina.flow import Flow
from jina.drivers.helper import array2pb
from jina.proto import jina_pb2, uid


@pytest.mark.parametrize('random_workspace_name', ['JINA_TEST_WORKSPACE_BINARY_PB'])
def test_binarypb_in_flow(test_metas):
    def random_docs(num_docs, chunks_per_doc=5, embed_dim=10, jitter=1):
        c_id = 3 * num_docs  # avoid collision with docs
        for j in range(num_docs):
            d = jina_pb2.Document()
            d.tags['id'] = j
            d.text = b'hello world'
            d.embedding.CopyFrom(array2pb(np.random.random([embed_dim + np.random.randint(0, jitter)])))
            d.id = uid.new_doc_id(d)
            for k in range(chunks_per_doc):
                c = d.chunks.add()
                c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
                c.embedding.CopyFrom(array2pb(np.random.random([embed_dim + np.random.randint(0, jitter)])))
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
        for d, d0 in zip(req.docs, docs):
            assert d.embedding.buffer == d0.embedding.buffer

    with f:
        f.search(docs, output_fn=validate, override_doc_id=False)
