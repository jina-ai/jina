import time

import numpy as np

from jina.helper import cached_property
from jina.logging.profile import TimeContext
from jina.proto import *
from tests import random_docs


def test_cached_property():
    """Test the cached_property decorator"""
    new_value = "99999"

    class DummyClass:
        def __init__(self):
            self.value = "11111"

        def change_value_in_instance(self, value):
            self.value = value

        @cached_property
        def test_property(self):
            return self.value

        @property
        def test_uncached_property(self):
            return self.value

    testClass = DummyClass()
    first_cached_test_property = testClass.test_property
    first_uncached_test_property = testClass.test_uncached_property
    testClass.change_value_in_instance(new_value)
    second_cached_test_property = testClass.test_property
    second_uncached_test_property = testClass.test_uncached_property

    assert first_cached_test_property == second_cached_test_property
    assert first_cached_test_property == "11111"

    assert first_uncached_test_property != second_uncached_test_property
    assert first_uncached_test_property == "11111"
    assert second_uncached_test_property == "99999"


def test_time_context():
    with TimeContext('dummy') as tc:
        time.sleep(2)

    assert int(tc.duration) == 2
    assert tc.readable_duration == '2 seconds'


def test_hash():
    ds = random_docs(10)
    tmp = []
    for d in ds:
        h = get_doc_hash(d)
        id = get_doc_id(d)
        print(f'{id}: {h}')
        assert id2hash(id) == h
        assert hash2id(h) == id
        tmp.append(h)

    tmp = np.array(tmp)
    assert tmp.dtype == np.int64
