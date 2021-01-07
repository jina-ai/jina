from typing import Dict

import numpy as np
import pytest

from jina import Document
from jina.drivers.craft import CraftDriver
from jina.executors.crafters import BaseCrafter
from jina.types.ndarray.generic import NdArray


@pytest.fixture(scope='function')
def docs():
    doc1 = Document(content='valid')
    doc2 = Document(content='invalid')
    return [doc1, doc2]


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


def test_craft_driver(docs):
    driver = SimpleCraftDriver()
    executor = MockCrafter()
    driver.attach(executor=executor, runtime=None)
    driver._apply_all(docs[:1])
    np.testing.assert_equal(NdArray(docs[0].blob).value, np.array([0.0, 0.0, 0.0]))
    assert docs[0].weight == 10
    with pytest.raises(AttributeError) as error:
        driver._apply_all(docs[1:2])
        assert error.value.__str__() == '\'non_existing_key\' is not recognized'
