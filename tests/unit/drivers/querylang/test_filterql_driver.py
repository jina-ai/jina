import pytest
from jina.proto.jina_pb2 import Document
from jina.drivers.querylang.filter import FilterQL
from tests import JinaTestCase


class FilterQLTestCase(JinaTestCase):
    @pytest.mark.skip('Not sure behavior')
    def test_filterql_driver(self):
        driver = FilterQL({'id__exact': 1})
        doc1 = Document()
        doc1.id = 1
        doc2 = Document()
        doc2.id = 2
        driver.apply(doc1)
        docs = [doc1, doc2]
        for doc in docs:
            driver.apply(doc)
