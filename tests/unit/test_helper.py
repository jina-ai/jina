import random
import time
from types import SimpleNamespace

import numpy as np

from cli import _is_latest_version
from jina.clients.python import PyClient, pprint_routes
from jina.drivers.querylang.queryset.dunderkey import dunder_get
from jina.helper import cached_property
from jina.logging.profile import TimeContext
from jina.proto import jina_pb2
from jina.proto.uid import *
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


def test_np_int():
    a = random.randint(0, 100000)
    assert hash2bytes(np.int64(a)) == hash2bytes(a)


def test_hash():
    ds = random_docs(10)
    tmp = []
    for d in ds:
        h = new_doc_hash(d)
        id = new_doc_id(d)
        print(f'{id}: {h}')
        assert id2hash(id) == h
        assert hash2id(h) == id
        tmp.append(h)

    tmp = np.array(tmp)
    assert tmp.dtype == np.int64


def test_random_docs():
    ds = random_docs(100)
    PyClient.check_input(ds)


def test_dunder_get():
    a = SimpleNamespace()
    a.b = {'c': 1}
    assert dunder_get(a, 'b__c') == 1


def test_check_update():
    assert _is_latest_version()
    # now mock it as old version
    import jina
    jina.__version__ = '0.1.0'
    assert not _is_latest_version()


def test_wrap_func():
    from jina.executors import BaseExecutor
    from jina.executors.encoders import BaseEncoder

    class DummyEncoder(BaseEncoder):
        def train(self):
            pass

    class MockEnc(DummyEncoder):
        pass

    class MockMockEnc(MockEnc):
        pass

    class MockMockMockEnc(MockEnc):
        def train(self):
            pass

    def check_override(cls, method):
        is_inherit = any(getattr(cls, method) == getattr(i, method, None) for i in cls.mro()[1:])
        is_parent_method = any(hasattr(i, method) for i in cls.mro()[1:])
        is_override = not is_inherit and is_parent_method
        return is_override

    # newly created
    assert not check_override(BaseExecutor, 'train')

    assert not check_override(BaseEncoder, 'train')
    assert check_override(DummyEncoder, 'train')
    assert not check_override(MockEnc, 'train')
    assert not check_override(MockMockEnc, 'train')
    assert check_override(MockMockMockEnc, 'train')


def test_pprint_routes(capfd):
    result = []
    r = jina_pb2.Route()
    r.status.code = jina_pb2.Status.ERROR
    r.status.exception.stacks.extend(['r1\nline1', 'r2\nline2'])
    result.append(r)
    r = jina_pb2.Route()
    r.status.code = jina_pb2.Status.ERROR_CHAINED
    r.status.exception.stacks.extend(['line1', 'line2'])
    result.append(r)
    r = jina_pb2.Route()
    r.status.code = jina_pb2.Status.SUCCESS
    result.append(r)
    pprint_routes(result)
    out, err = capfd.readouterr()
    assert out == '''+-----+------+------------+
| \x1b[1mPod\x1b[0m | \x1b[1mTime\x1b[0m | \x1b[1mException\x1b[0m  |
+-----+------+------------+
| 🔴  | 0ms  | r1         |
|     |      | line1r2    |
|     |      | line2      |
+-----+------+------------+
| ⚪  | 0ms  | line1line2 |
+-----+------+------------+
| 🟢  | 0ms  |            |
+-----+------+------------+
'''
