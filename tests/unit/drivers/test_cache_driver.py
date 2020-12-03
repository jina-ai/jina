import os
from typing import Any

import numpy as np
import pytest

from jina import DocumentSet
from jina.drivers.cache import BaseCacheDriver
from jina.executors.indexers.cache import DocIDCache
from jina.proto import jina_pb2
from jina.types.document import uid
from tests import random_docs


class MockCacheDriver(BaseCacheDriver):

    @property
    def exec_fn(self):
        return self._exec_fn

    def on_hit(self, req_doc: 'jina_pb2.DocumentProto', hit_result: Any) -> None:
        raise NotImplementedError

    @property
    def docs(self):
        return DocumentSet(list(random_docs(10)))


def test_cache_driver_twice(tmp_path):
    filename = tmp_path / 'test-tmp.bin'
    docs = DocumentSet(list(random_docs(10)))
    driver = MockCacheDriver()
    with DocIDCache(filename) as executor:
        assert not executor.handler_mutex
        driver.attach(executor=executor, pea=None)
        driver._traverse_apply(docs)

        with pytest.raises(NotImplementedError):
            # duplicate docs
            driver._traverse_apply(docs)

        # new docs
        docs = list(random_docs(10))
        driver._traverse_apply(docs)

        # check persistence
        assert os.path.exists(filename)


def test_cache_driver_tmpfile():
    docs = list(random_docs(10))
    driver = MockCacheDriver()
    with DocIDCache() as executor:
        assert not executor.handler_mutex
        driver.attach(executor=executor, pea=None)

        driver._traverse_apply(docs)

        with pytest.raises(NotImplementedError):
            # duplicate docs
            driver._traverse_apply(docs)

        # new docs
        docs = list(random_docs(10))
        driver._traverse_apply(docs)

    # check persistence
    assert os.path.exists(executor.index_abspath)


def test_cache_driver_from_file(tmp_path):
    filename = tmp_path / 'test-tmp.bin'
    docs = list(random_docs(10))
    with open(filename, 'wb') as fp:
        fp.write(np.array([uid.id2hash(d.id) for d in docs], dtype=np.int64).tobytes())

    driver = MockCacheDriver()
    with DocIDCache(filename) as executor:
        assert not executor.handler_mutex
        driver.attach(executor=executor, pea=None)

        with pytest.raises(NotImplementedError):
            # duplicate docs
            driver._traverse_apply(docs)

        # new docs
        docs = list(random_docs(10))
        driver._traverse_apply(docs)

        # check persistence
        assert os.path.exists(filename)
