from jina.executors import BaseExecutor
from jina.executors.indexers.vector import NumpyIndexer
from jina.executors.metas import get_default_metas


def test_set_batch_size():
    batch_size = 325
    metas = get_default_metas()
    metas['batch_size'] = batch_size
    indexer = NumpyIndexer(index_filename=f'test.gz', metas=metas)
    assert indexer.batch_size == batch_size


def test_set_dummy_meta():
    dummy = 325
    metas = get_default_metas()
    metas['dummy'] = dummy
    executor = BaseExecutor(metas=metas)
    assert executor.dummy == dummy


def test_set_is_trained_meta():
    metas = get_default_metas()
    metas['is_trained'] = True
    executor = BaseExecutor(metas=metas)
    assert executor.is_trained
