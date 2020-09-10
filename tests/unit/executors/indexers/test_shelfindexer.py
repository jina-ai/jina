from jina.executors.indexers.keyvalue import ShelfPbIndexer
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import random_docs


def test_shelf():
    docs = list(random_docs(10))
    with ShelfPbIndexer('test-shelf') as spi:
        spi.add(docs)

    with ShelfPbIndexer('test-shelf') as spi:
        print(spi.index_abspath)
        assert spi.query(1) == docs[1]
        assert spi.query(11) is None
        assert spi.size == 10


def test_shelf_in_flow():
    docs = list(random_docs(10))
    f = Flow(callback_on_body=True).add(uses='shelfpb.yml')

    with f:
        f.index(docs)

    d = jina_pb2.Document()
    d.id = 1

    def validate(req):
        assert req.docs[0].embedding == docs[0].embedding

    with f:
        f.search([d], output_fn=validate)
