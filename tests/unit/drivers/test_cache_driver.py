import os
import pickle
from typing import Any

import pytest

from jina import DocumentSet
from jina.drivers.cache import BaseCacheDriver
from jina.executors import BaseExecutor
from jina.executors.indexers.cache import DocIDCache, ID_KEY, CONTENT_HASH_KEY
from jina.proto import jina_pb2
from jina.types.document import Document, UniqueId
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


def test_cache_driver_twice(tmpdir):
    docs = DocumentSet(list(random_docs(10)))
    driver = MockCacheDriver()
    # FIXME DocIdCache doesn't use tmpdir, it saves in curdir
    with DocIDCache(tmpdir) as executor:
        assert not executor.handler_mutex
        driver.attach(executor=executor, runtime=None)
        driver._traverse_apply(docs)

        with pytest.raises(NotImplementedError):
            # duplicate docs
            driver._traverse_apply(docs)

        # new docs
        docs = list(random_docs(10, start_id=100))
        driver._traverse_apply(docs)
        filename = executor.save_abspath

    # check persistence
    assert os.path.exists(filename)


def test_cache_driver_tmpfile():
    docs = list(random_docs(10, embedding=False))
    driver = MockCacheDriver()
    with DocIDCache(field=ID_KEY) as executor:
        assert not executor.handler_mutex
        driver.attach(executor=executor, runtime=None)

        driver._traverse_apply(docs)

        with pytest.raises(NotImplementedError):
            # duplicate docs
            driver._traverse_apply(docs)

        # new docs
        docs = list(random_docs(10, start_id=100, embedding=False))
        driver._traverse_apply(docs)

    assert os.path.exists(executor.index_abspath)


def test_cache_driver_from_file(tmp_path):
    filename = 'test-tmp.bin'
    docs = list(random_docs(10, embedding=False))
    pickle.dump([doc.id for doc in docs], open(f'{filename}.ids', 'wb'))
    pickle.dump([doc.content_hash for doc in docs], open(f'{filename}.cache', 'wb'))

    driver = MockCacheDriver()
    with DocIDCache(filename, field=CONTENT_HASH_KEY) as executor:
        assert not executor.handler_mutex
        driver.attach(executor=executor, runtime=None)

        with pytest.raises(NotImplementedError):
            # duplicate docs
            driver._traverse_apply(docs)

        # new docs
        docs = list(random_docs(10, start_id=100))
        driver._traverse_apply(docs)

    # check persistence
    assert os.path.exists(executor.save_abspath)


class MockBaseCacheDriver(BaseCacheDriver):

    @property
    def exec_fn(self):
        return self._exec_fn

    def on_hit(self, req_doc: 'jina_pb2.DocumentProto', hit_result: Any) -> None:
        raise NotImplementedError


def test_cache_content_driver_same_content(tmpdir):
    doc1 = Document(id=1)
    doc1.text = 'blabla'
    doc1.update_content_hash()
    docs1 = DocumentSet([doc1])

    doc2 = Document(id=2)
    doc2.text = 'blabla'
    doc2.update_content_hash()
    docs2 = DocumentSet([doc2])
    assert doc1.content_hash == doc2.content_hash

    driver = MockBaseCacheDriver()
    filename = None

    with DocIDCache(tmpdir, field=CONTENT_HASH_KEY) as executor:
        driver.attach(executor=executor, runtime=None)
        driver._traverse_apply(docs1)

        with pytest.raises(NotImplementedError):
            driver._traverse_apply(docs2)

        assert executor.size == 1
        filename = executor.save_abspath

    # update
    old_doc = Document(id=9999)
    old_doc.text = 'blabla'
    old_doc.update_content_hash()

    new_string = 'blabla-new'
    doc1.text = new_string
    doc1.update_content_hash()
    with BaseExecutor.load(filename) as executor:
        executor.update([UniqueId(1)], [doc1.content_hash])

    with BaseExecutor.load(filename) as executor:
        assert executor.query(doc1.content_hash) is True
        assert executor.query(old_doc.content_hash) is None

    # delete
    with BaseExecutor.load(filename) as executor:
        executor.delete([UniqueId(doc1.id)])

    with BaseExecutor.load(filename) as executor:
        assert executor.query(doc1.content_hash) is None


def test_cache_content_driver_same_id(tmp_path):
    filename = tmp_path / 'docidcache.bin'
    doc1 = Document(id=1)
    doc1.text = 'blabla'
    doc1.update_content_hash()
    docs1 = DocumentSet([doc1])

    doc2 = Document(id=1)
    doc2.text = 'blabla2'
    doc2.update_content_hash()
    docs2 = DocumentSet([doc2])

    driver = MockBaseCacheDriver()

    with DocIDCache(filename, field=CONTENT_HASH_KEY) as executor:
        driver.attach(executor=executor, runtime=None)
        driver._traverse_apply(docs1)
        driver._traverse_apply(docs2)
        assert executor.size == 2
