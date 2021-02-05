import os
import pickle
from typing import Any

import pytest

from jina import DocumentSet
from jina.drivers.cache import BaseCacheDriver
from jina.drivers.delete import DeleteDriver
from jina.executors import BaseExecutor
from jina.executors.indexers.cache import DocCache, ID_KEY, CONTENT_HASH_KEY
from jina.proto import jina_pb2
from jina.types.document import Document
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


def test_cache_driver_twice(tmpdir, test_metas):
    docs = DocumentSet(list(random_docs(10)))
    driver = MockCacheDriver()
    # FIXME DocCache doesn't use tmpdir, it saves in curdir
    with DocCache(tmpdir, metas=test_metas) as executor:
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


def test_cache_driver_tmpfile(tmpdir, test_metas):
    docs = list(random_docs(10, embedding=False))
    driver = MockCacheDriver()
    with DocCache(tmpdir, field=ID_KEY, metas=test_metas) as executor:
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


def test_cache_driver_from_file(tmpdir, test_metas):
    test_metas['name'] = 'cachename'
    filename = 'cache'
    folder = os.path.join(test_metas["workspace"])
    bin_full_path = os.path.join(folder, filename)
    docs = list(random_docs(10, embedding=False))
    pickle.dump({doc.id: doc.content_hash for doc in docs}, open(f'{bin_full_path}.ids', 'wb'))
    pickle.dump({doc.content_hash: doc.id for doc in docs}, open(f'{bin_full_path}.cache', 'wb'))

    driver = MockCacheDriver()
    with DocCache(filename, metas=test_metas, field=CONTENT_HASH_KEY) as executor:
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


class SimpleDeleteDriver(DeleteDriver):

    @property
    def exec_fn(self):
        return self._exec_fn


def test_cache_content_driver_same_content(tmpdir, test_metas):
    doc1 = Document(id='1')
    doc1.text = 'blabla'
    doc1.update_content_hash()
    docs1 = DocumentSet([doc1])

    doc2 = Document(id='2')
    doc2.text = 'blabla'
    doc2.update_content_hash()
    docs2 = DocumentSet([doc2])
    assert doc1.content_hash == doc2.content_hash

    driver = MockBaseCacheDriver()

    with DocCache(tmpdir, metas=test_metas, field=CONTENT_HASH_KEY) as executor:
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
        executor.update(['1'], [doc1.content_hash])

    with BaseExecutor.load(filename) as executor:
        assert executor.query(doc1.content_hash) is True
        assert executor.query(old_doc.content_hash) is False

    # delete
    with BaseExecutor.load(filename) as executor:
        executor.delete([doc1.id])

    with BaseExecutor.load(filename) as executor:
        assert executor.query(doc1.content_hash) is False


def test_cache_content_driver_same_id(tmp_path, test_metas):
    filename = os.path.join(tmp_path, 'DocCache.bin')
    doc1 = Document(id=1)
    doc1.text = 'blabla'
    doc1.update_content_hash()
    docs1 = DocumentSet([doc1])

    doc2 = Document(id=1)
    doc2.text = 'blabla2'
    doc2.update_content_hash()
    docs2 = DocumentSet([doc2])

    driver = MockBaseCacheDriver()

    with DocCache(filename, metas=test_metas, field=CONTENT_HASH_KEY) as executor:
        driver.attach(executor=executor, runtime=None)
        driver._traverse_apply(docs1)
        driver._traverse_apply(docs2)
        assert executor.size == 2


@pytest.mark.parametrize('field_type', [CONTENT_HASH_KEY, ID_KEY])
def test_cache_driver_update(tmpdir, test_metas, field_type, mocker):
    driver = MockBaseCacheDriver(method='update', traversal_paths=['r'])

    docs = [Document(text=f'doc_{i}') for i in range(5)]

    def validate_delete(self, keys, *args, **kwargs):
        assert len(keys) == len(docs)
        assert all([k == d.id for k, d in zip(keys, docs)])

    def validate_update(self, keys, values, *args, **kwargs):
        assert len(keys) == len(docs)
        assert len(values) == len(docs)
        assert all([k == d.id for k, d in zip(keys, docs)])
        if self.field == CONTENT_HASH_KEY:
            assert all([v == d.content_hash for v, d in zip(values, docs)])
        elif self.field == ID_KEY:
            assert all([v == d.id for v, d in zip(values, docs)])

    with DocCache(tmpdir, metas=test_metas, field=field_type) as e:
        mocker.patch.object(DocCache, 'update', validate_update)
        mocker.patch.object(DocCache, 'delete', validate_delete)
        driver.attach(executor=e, runtime=None)
        driver._apply_all(docs)


@pytest.mark.parametrize('field_type', [CONTENT_HASH_KEY, ID_KEY])
def test_cache_driver_delete(tmpdir, test_metas, field_type, mocker):
    docs = [Document(text=f'doc_{i}') for i in range(5)]

    driver = SimpleDeleteDriver()

    def validate_delete(self, keys, *args, **kwargs):
        assert len(keys) == len(docs)
        assert all([k == d.id for k, d in zip(keys, docs)])

    with DocCache(tmpdir, metas=test_metas, field=field_type) as e:
        mocker.patch.object(DocCache, 'delete', validate_delete)

        driver.attach(executor=e, runtime=None)
        mck = mocker.patch.object(driver, 'runtime', autospec=True)
        mck.request.ids = [d.id for d in docs]
        driver()
