from typing import Dict

import numpy as np
import pytest

from jina.drivers.craft import CraftDriver
from jina.executors.crafters import BaseCrafter
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


class MockCrafter(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {'text'}

    def craft(self, text: str, *args, **kwargs) -> Dict:
        if text == 'valid':
            return {'blob': np.array([0.0, 0.0, 0.0]), 'weight': 10}
        else:
            return {'non_existing_key': 1}


class SimpleCraftDriver(CraftDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def create_documents_to_craft():
    doc1 = jina_pb2.Document()
    # doc1.id = 1
    doc1.text = 'valid'
    doc2 = jina_pb2.Document()
    # doc2.id = 2
    doc2.text = 'invalid'
    return [doc1, doc2]


def test_craft_driver():
    docs = create_documents_to_craft()
    driver = SimpleCraftDriver()
    executor = MockCrafter()
    driver.attach(executor=executor, pea=None)
    driver._apply_all(docs[:1])
    np.testing.assert_equal(GenericNdArray(docs[0].blob).value, np.array([0.0, 0.0, 0.0]))
    assert docs[0].weight == 10
    with pytest.raises(AttributeError) as error:
        driver._apply_all(docs[1:2])
    assert error.value.__str__() == '\'Document\' object has no attribute \'non_existing_key\''
