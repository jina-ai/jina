import random
import time
from types import SimpleNamespace

import pytest

from cli import _is_latest_version
from jina import NdArray, Request
from jina.clients.helper import _safe_callback, pprint_routes
from jina.drivers.querylang.queryset.dunderkey import dunder_get
from jina.excepts import BadClientCallback
from jina.helper import cached_property, convert_tuple_to_list
from jina.jaml.helper import _complete_path
from jina.logging.profile import TimeContext
from jina.proto import jina_pb2
from jina.types.document.uid import *
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
    assert int2bytes(np.int64(a)) == int2bytes(a)


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
    r = jina_pb2.RouteProto()
    r.status.code = jina_pb2.StatusProto.ERROR
    r.status.exception.stacks.extend(['r1\nline1', 'r2\nline2'])
    result.append(r)
    r = jina_pb2.RouteProto()
    r.status.code = jina_pb2.StatusProto.ERROR_CHAINED
    r.status.exception.stacks.extend(['line1', 'line2'])
    result.append(r)
    r = jina_pb2.RouteProto()
    r.status.code = jina_pb2.StatusProto.SUCCESS
    result.append(r)
    rr = Request()
    rr.routes.extend(result)
    pprint_routes(rr)
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


def test_convert_tuple_to_list():
    d = {'1': (1, 2), 2: {'a': (3, 4)}}
    convert_tuple_to_list(d)
    assert d == {'1': [1, 2], 2: {'a': [3, 4]}}


def test_safe_callback():
    def t1():
        raise NotImplementedError

    st1 = _safe_callback(t1, continue_on_error=True, logger=default_logger)
    st1()

    st1 = _safe_callback(t1, continue_on_error=False, logger=default_logger)
    with pytest.raises(BadClientCallback):
        st1()


def test_random_docs():
    np.random.seed(42)
    nr_docs = 10
    docs1 = list(random_docs(nr_docs))
    np.random.seed(42)
    docs2 = list(random_docs(nr_docs))
    doc_ids = []
    chunk_ids = []
    for d2, d1 in zip(docs2, docs1):
        np.testing.assert_almost_equal(d2.embedding, NdArray(d1.embedding).value)
        doc_ids.append(int(d1.id))
        assert d2.text == d1.text
        assert d2.tags['id'] == d1.tags['id']
        for c2, c1 in zip(d2.chunks, d1.chunks):
            np.testing.assert_almost_equal(c2.embedding, NdArray(c1.embedding).value)
            chunk_ids.append(int(c1.id))
            assert c2.text == c1.text
            assert c2.tags['id'] == c1.tags['id']
            assert c2.tags['parent_id'] == c1.tags['parent_id']
    assert len(set(doc_ids)) == len(doc_ids)
    assert len(set(chunk_ids)) == len(chunk_ids)
    assert len(set(doc_ids).intersection(set(chunk_ids))) == 0


def test_complete_path_success():
    assert _complete_path('test_helper.py')
    assert _complete_path('helper.py')
    assert _complete_path('bash')


def test_complete_path_not_found():
    with pytest.raises(FileNotFoundError):
        assert _complete_path('unknown.yaml')
