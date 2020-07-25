from jina.proto.jina_pb2 import Document
from jina.drivers.querylang.filter import FilterQL
from tests import JinaTestCase


class FilterQLTestCase(JinaTestCase):
    def test_filterql_driver(self):
        driver = FilterQL({'id__exact': 2})
        doc1 = Document()
        doc1.id = 1
        doc2 = Document()
        doc2.id = 2
        self.assertTrue(driver._apply(doc1))
        self.assertFalse(driver._apply(doc2))
        docs = [doc1, doc2]
        self.assertEqual(len(docs), 2)
        del docs[0]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].id, 2)
