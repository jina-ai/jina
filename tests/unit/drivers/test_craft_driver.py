from typing import Dict

import numpy as np
import pytest

from jina import Document, DocumentSet
from jina.drivers.craft import CraftDriver
from jina.executors.crafters import BaseCrafter
from jina.types.ndarray.generic import NdArray


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


@pytest.fixture(scope='function')
def craft_driver():
    driver = SimpleCraftDriver()
    executor = MockCrafter()
    driver.attach(executor=executor, runtime=None)
    return driver


def test_valid_document(craft_driver):
    valid_document = Document(content='valid')
    docs = DocumentSet([valid_document])
    craft_driver._apply_all(docs)
    np.testing.assert_equal(
        NdArray(valid_document.blob).value, np.array([0.0, 0.0, 0.0])
    )
    assert valid_document.weight == 10


def test_invalid_document(craft_driver):
    invalid_document = Document(content='invalid')
    docs = DocumentSet([invalid_document])
    with pytest.raises(AttributeError) as error:
        craft_driver._apply_all(docs)
        assert error.value.__str__() == '\'non_existing_key\' is not recognized'
