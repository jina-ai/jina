import os
import time
from types import SimpleNamespace

import numpy as np
import pytest

from cli import _is_latest_version
from jina import Executor, __default_endpoint__
from jina.clients.helper import _safe_callback, pprint_routes
from jina.excepts import BadClientCallback, NotSupportedError, NoAvailablePortError
from jina.executors.decorators import requests
from jina.helper import (
    cached_property,
    convert_tuple_to_list,
    deprecated_alias,
    is_yaml_filepath,
    random_port,
    find_request_binding,
    dunder_get,
    get_ci_vendor,
)
from jina.jaml.helper import complete_path
from jina.logging.predefined import default_logger
from jina.logging.profile import TimeContext
from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray
from jina.types.request import Request
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


def test_dunder_get():
    a = SimpleNamespace()
    a.b = {'c': 1, 'd': {'e': 'f', 'g': [0, 1, {'h': 'i'}]}}
    assert dunder_get(a, 'b__c') == 1
    assert dunder_get(a, 'b__d__e') == 'f'
    assert dunder_get(a, 'b__d__g__0') == 0
    assert dunder_get(a, 'b__d__g__2__h') == 'i'


def test_check_update():
    assert _is_latest_version()
    # now mock it as old version
    import jina

    jina.__version__ = '0.1.0'
    assert not _is_latest_version()


def test_wrap_func():
    from jina import Executor

    class DummyEncoder(Executor):
        def __init__(self):
            pass

    class MockEnc(DummyEncoder):
        pass

    class MockMockEnc(MockEnc):
        pass

    class MockMockMockEnc(MockEnc):
        def __init__(self):
            pass

    def check_override(cls, method):
        is_inherit = any(
            getattr(cls, method) == getattr(i, method, None) for i in cls.mro()[1:]
        )
        is_parent_method = any(hasattr(i, method) for i in cls.mro()[1:])
        is_override = not is_inherit and is_parent_method
        return is_override

    assert check_override(DummyEncoder, '__init__')
    assert not check_override(MockEnc, '__init__')
    assert not check_override(MockMockEnc, '__init__')
    assert check_override(MockMockMockEnc, '__init__')


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
    assert '⚪' in out
    assert '🟢' in out
    assert 'Pod' in out
    assert 'Time' in out
    assert 'Exception' in out
    assert 'r1' in out
    assert 'line1r2' in out
    assert 'line2' in out
    assert 'line1line2' in out


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
        doc_ids.append((d1.id))
        assert d2.text == d1.text
        assert d2.tags['id'] == d1.tags['id']
        for c2, c1 in zip(d2.chunks, d1.chunks):
            np.testing.assert_almost_equal(c2.embedding, NdArray(c1.embedding).value)
            chunk_ids.append((c1.id))
            assert c2.text == c1.text
            assert c2.tags['id'] == c1.tags['id']
            assert c2.tags['parent_id'] == c1.tags['parent_id']
    assert len(set(doc_ids)) == len(doc_ids)
    assert len(set(chunk_ids)) == len(chunk_ids)
    assert len(set(doc_ids).intersection(set(chunk_ids))) == 0


def test_complete_path_success():
    assert complete_path('test_helper.py')
    assert complete_path('helper.py')
    assert complete_path('bash')


def test_complete_path_not_found():
    with pytest.raises(FileNotFoundError):
        assert complete_path('unknown.yaml')


def test_deprecated_decor():
    @deprecated_alias(barbar=('bar', 0), foofoo=('foo', 1))
    def dummy(bar, foo):
        return bar, foo

    # normal
    assert dummy(bar=1, foo=2) == (1, 2)

    # deprecated warn
    with pytest.deprecated_call():
        assert dummy(barbar=1, foo=2) == (1, 2)

    # deprecated HARD
    with pytest.raises(NotSupportedError):
        dummy(bar=1, foofoo=2)


@pytest.mark.parametrize(
    'val',
    [
        'merge_and_topk.yml',
        'merge_and_topk.yaml',
        'da.yaml',
        'd.yml',
        '/da/da.yml',
        'das/das.yaml',
        '1234.yml',
        '1234.yml ',
        ' 1234.yml ',
    ],
)
def test_yaml_filepath_validate_good(val):
    assert is_yaml_filepath(val)


@pytest.mark.parametrize(
    'val',
    [
        ' .yml',
        'a',
        ' uses: yaml',
        'ayaml',
        '''
    shards: $JINA_SHARDS_INDEXERS
    host: $JINA_REDIS_INDEXER_HOST
    port_expose: 8000
    polling: all
    timeout_ready: 100000 # larger timeout as in query time will read all the data
    uses_after: merge_and_topk.yml
                                 ''',
    ],
)
def test_yaml_filepath_validate_bad(val):
    assert not is_yaml_filepath(val)


@pytest.fixture
def config():
    os.environ['JINA_RANDOM_PORTS'] = "True"
    yield
    del os.environ['JINA_RANDOM_PORTS']


def test_random_port(config):
    assert os.environ['JINA_RANDOM_PORTS']
    port = random_port()
    assert 49153 <= port <= 65535


@pytest.fixture
def config_few_ports():
    os.environ['JINA_RANDOM_PORTS'] = "True"
    os.environ['JINA_RANDOM_PORT_MIN'] = "49300"
    os.environ['JINA_RANDOM_PORT_MAX'] = "49301"
    yield
    del os.environ['JINA_RANDOM_PORT_MIN']
    del os.environ['JINA_RANDOM_PORT_MAX']
    del os.environ['JINA_RANDOM_PORTS']


def test_random_port_max_failures_for_tests_only(config_few_ports):
    from jina.helper import random_port as random_port_with_max_failures

    with pytest.raises(NoAvailablePortError):
        random_port_with_max_failures()
        random_port_with_max_failures()
        random_port_with_max_failures()
        random_port_with_max_failures()


class MyDummyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        pass

    @requests(on='index')
    def bar(self, **kwargs):
        pass

    @requests(on='search')
    def bar2(self, **kwargs):
        pass

    def foo2(self):
        pass


def test_find_request_binding():
    r = find_request_binding(MyDummyExecutor)
    assert r[__default_endpoint__] == 'foo'
    assert r['index'] == 'bar'
    assert r['search'] == 'bar2'
    assert 'foo2' not in r.values()


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' not in os.environ, reason='this test is only validate on CI'
)
def test_ci_vendor():
    assert get_ci_vendor() == 'GITHUB_ACTIONS'
