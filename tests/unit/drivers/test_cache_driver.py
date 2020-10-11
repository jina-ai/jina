import numpy as np

from jina.drivers.cache import UniqueDocDriver
from tests import random_docs, rm_files


def test_cache_driver_twice():
    cache_file = 'test-cache.bin'

    docs = list(random_docs(10))
    driver = UniqueDocDriver(cache_file)
    driver._apply_all(docs)
    assert len(docs) == 10
    # duplicate docs
    driver._apply_all(docs)
    assert len(docs) == 0

    # new docs
    docs = list(random_docs(10))
    driver._apply_all(docs)
    assert len(docs) == 10

    # in total there should be 20 unique doc ids
    with open(cache_file, 'rb') as fp:
        ids = np.frombuffer(fp.read(), dtype=np.int64)
        assert len(ids) == 20

    rm_files(['test-cache.bin'])


