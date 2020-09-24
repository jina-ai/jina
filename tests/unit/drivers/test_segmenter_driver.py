from typing import Dict, List
import numpy as np
import pytest

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
            return [{'blob': np.array([0.0, 0.0, 0.0]), 'weight': 0, 'mime_type': "text/plain"},
                    {'blob': np.array([1.0, 1.0, 1.0]), 'weight': 1},
                    {'blob': np.array([2.0, 2.0, 2.0]), 'weight': 2, 'length': 10, 'parent_id': 50, 'id': 10}]
        else:
            return [{'non_existing_key': 1}]


class SimpleSegmentDriver(SegmentDriver):

    def __init__(self, first_chunk_id, *args, **kwargs):
        super().__init__(first_chunk_id=first_chunk_id, random_chunk_id=False, *args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def test_segment_driver():
    valid_doc = jina_pb2.Document()
    valid_doc.id = 1
    valid_doc.text = 'valid'
    valid_doc.length = 2
    valid_doc.mime_type = 'image/png'

    driver = SimpleSegmentDriver(first_chunk_id=3)
    executor = MockSegmenter()
    driver.attach(executor=executor, pea=None)
    driver._apply(valid_doc)

    assert valid_doc.length == 2

    assert valid_doc.chunks[0].id == 3
    assert valid_doc.chunks[0].parent_id == valid_doc.id
    assert valid_doc.chunks[0].blob == array2pb(np.array([0.0, 0.0, 0.0]))
    assert valid_doc.chunks[0].weight == 0
    assert valid_doc.chunks[0].length == 3
    assert valid_doc.chunks[0].mime_type == 'text/plain'

    assert valid_doc.chunks[1].id == 4
    assert valid_doc.chunks[1].parent_id == valid_doc.id
    assert valid_doc.chunks[1].blob == array2pb(np.array([1.0, 1.0, 1.0]))
    assert valid_doc.chunks[1].weight == 1
    assert valid_doc.chunks[1].length == 3
    assert valid_doc.chunks[1].mime_type == 'image/png'

    assert valid_doc.chunks[2].id == 5
    assert valid_doc.chunks[2].parent_id == valid_doc.id
    assert valid_doc.chunks[2].blob == array2pb(np.array([2.0, 2.0, 2.0]))
    assert valid_doc.chunks[2].weight == 2
    assert valid_doc.chunks[2].length == 3



def test_broken_document():
    driver = SimpleSegmentDriver(first_chunk_id=3)
    executor = MockSegmenter()
    driver.attach(executor=executor, pea=None)

    invalid_doc = jina_pb2.Document()
    invalid_doc.id = 2
    invalid_doc.text = 'invalid'
    invalid_doc.length = 2

    assert invalid_doc.length == 2

    with pytest.raises(AttributeError):
        driver._apply(invalid_doc)
