import time
from binascii import unhexlify

from jina.helper import cached_property
from jina.logging.profile import TimeContext
from jina.proto import HashProto
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


def test_hash_counter():
    num_docs = 10
    num_chunks_per_doc = 5
    get_docs = lambda: random_docs(num_docs, num_chunks_per_doc)

    hc = HashProto()
    hashes = set(hc(d) for d in get_docs())
    assert len(hashes) == num_docs

    hc = HashProto()
    hashes = set(hc(c) for d in get_docs() for c in d.chunks)
    # all docs have same text, they should be hashed into one
    assert len(hashes) == num_docs * num_chunks_per_doc

    # and now with field mask
    hc = HashProto(paths=['text'])
    hashes = set(hc(d) for d in get_docs())
    # all docs have same text, they should be hashed into one
    assert len(hashes) == 1

    hc = HashProto(paths=['parent_id'])
    hashes = set(hc(c) for d in get_docs() for c in d.chunks)
    # they have different parents
    assert len(hashes) == num_docs

    # no chunk set tags, so they will be hashed into one
    hc = HashProto(paths=['tags'])
    hashes = set(hc(c) for d in get_docs() for c in d.chunks)
    assert len(hashes) == 1

    # no chunk set tags, but as the context hash is given, they will be hashed into num_docs
    hc_d = HashProto()
    hc = HashProto(paths=['tags'])
    hashes = set(hc(c, context_hash=unhexlify(hc_d(d))) for d in get_docs() for c in d.chunks)
    assert len(hashes) == num_docs
