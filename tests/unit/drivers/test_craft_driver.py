from typing import Dict

import numpy as np
import pytest

from jina import Document, DocumentArray
from jina.drivers.craft import CraftDriver
from jina.executors.decorators import single
from jina.executors.crafters import BaseCrafter
from jina.types.ndarray.generic import NdArray


class MockCrafter(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single
    def craft(self, text: str, *args, **kwargs) -> Dict:
        if text == 'valid':
            return {'blob': np.array([0.0, 0.0, 0.0]), 'weight': 10}
        else:
            return {'non_existing_key': 1}


class MockImageCrafter(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single
    def craft(self, blob: np.ndarray, *args, **kwargs) -> Dict:
        assert len(blob.shape) == 3
        assert blob.shape[0] == 1
        return {'blob': blob}


class SimpleCraftDriver(CraftDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture()
def text_craft_executor():
    return MockCrafter()


@pytest.fixture()
def image_craft_executor():
    return MockImageCrafter()


@pytest.fixture()
def craft_driver():
    driver = SimpleCraftDriver()
    executor = MockCrafter()
    driver.attach(executor=executor, runtime=None)
    return driver


def test_valid_document(craft_driver, text_craft_executor):
    craft_driver.attach(executor=text_craft_executor, runtime=None)
    valid_document = Document(content='valid')
    docs = DocumentArray([valid_document])
    craft_driver._apply_all(docs)
    np.testing.assert_equal(
        NdArray(valid_document.blob).value, np.array([0.0, 0.0, 0.0])
    )
    assert valid_document.weight == 10


def test_invalid_document(craft_driver, text_craft_executor):
    craft_driver.attach(executor=text_craft_executor, runtime=None)
    invalid_document = Document(content='invalid')
    docs = DocumentArray([invalid_document])
    with pytest.raises(AttributeError) as error:
        craft_driver._apply_all(docs)
        assert error.value.__str__() == '\'non_existing_key\' is not recognized'


def test_image_crafting(craft_driver, image_craft_executor):
    craft_driver.attach(executor=image_craft_executor, runtime=None)
    blob1 = np.random.random((1, 32, 64))
    blob2 = np.random.random((1, 64, 32))
    docs = DocumentArray([Document(blob=blob1), Document(blob=blob2)])
    craft_driver._apply_all(docs)
    np.testing.assert_equal(docs[0].blob, blob1)
    np.testing.assert_equal(docs[1].blob, blob2)
