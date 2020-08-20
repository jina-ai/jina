from typing import Dict, List
import numpy as np
from jina.drivers.craft import SegmentDriver
from jina.executors.crafters import BaseSegmenter
from jina.drivers.helper import array2pb
from jina.proto import jina_pb2
from tests import JinaTestCase


class MockSegmenter(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {'text'}

    def craft(self, text: str, *args, **kwargs) -> List[Dict]:
        if text == 'valid':
            # length, parent_id and id are protected keys that won't affect the segments
            return [{'blob': np.array([0.0, 0.0, 0.0]), 'weight': 0},
                    {'blob': np.array([1.0, 1.0, 1.0]), 'weight': 1},
                    {'blob': np.array([2.0, 2.0, 2.0]), 'weight': 2, 'length': 10, 'parent_id': 50, 'id': 10}]
        else:
            return [{'non_existing_key': 1}]


class SimpleSegmentDriver(SegmentDriver):

    def __init__(self, first_chunk_id,  *args, **kwargs):
        super().__init__(first_chunk_id=first_chunk_id, random_chunk_id=False, *args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def create_documents_to_segment():
    doc1 = jina_pb2.Document()
    doc1.id = 1
    doc1.text = 'valid'
    doc1.length = 2
    doc2 = jina_pb2.Document()
    doc2.id = 2
    doc2.text = 'invalid'
    doc2.length = 2
    return [doc1, doc2]


class SegmentDriverTestCase(JinaTestCase):

    def test_segment_driver(self):
        docs = create_documents_to_segment()
        driver = SimpleSegmentDriver(first_chunk_id=3)
        executor = MockSegmenter()
        driver.attach(executor=executor, pea=None)
        driver._apply(docs[0])

        assert docs[0].length == 2
        assert docs[1].length == 2

        assert docs[0].chunks[0].id == 3
        assert docs[0].chunks[0].parent_id == docs[0].id
        assert docs[0].chunks[0].blob == array2pb(np.array([0.0, 0.0, 0.0]))
        assert docs[0].chunks[0].weight == 0
        assert docs[0].chunks[0].length == 3

        assert docs[0].chunks[1].id == 4
        assert docs[0].chunks[1].parent_id == docs[0].id
        assert docs[0].chunks[1].blob == array2pb(np.array([1.0, 1.0, 1.0]))
        assert docs[0].chunks[1].weight == 1
        assert docs[0].chunks[1].length == 3

        assert docs[0].chunks[2].id == 5
        assert docs[0].chunks[2].parent_id == docs[0].id
        assert docs[0].chunks[2].blob == array2pb(np.array([2.0, 2.0, 2.0]))
        assert docs[0].chunks[2].weight == 2
        assert docs[0].chunks[2].length == 3

        with self.assertRaises(AttributeError) as error:
            driver._apply(docs[1])
        assert error.exception.__str__() == '\'Document\' object has no attribute \'non_existing_key\''
