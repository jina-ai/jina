from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import random_docs


def test_binary_pb():
    num_docs = 100
    docs = list(random_docs(num_docs, jitter=50))
    with BinaryPbIndexer('test-shelf') as spi:
        spi.add(docs)
        spi.save()

    with BinaryPbIndexer.load(spi.save_abspath) as spi:
        assert spi.size == num_docs
        for j in range(num_docs):
            assert spi.query(j) == docs[j]


def test_binarypb_in_flow():
    docs = list(random_docs(10))
    f = Flow(callback_on_body=True).add(uses='binarypb.yml')

    with f:
        f.index(docs, override_doc_id=False)

    d = jina_pb2.Document()
    d.id = 1

    def validate(req):
        for d, d0 in zip(req.docs, docs):
          assert d.embedding.buffer == d0.embedding.buffer

    with f:
        f.search(docs, output_fn=validate, override_doc_id=False)

