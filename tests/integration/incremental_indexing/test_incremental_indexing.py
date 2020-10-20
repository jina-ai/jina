import os

from jina.flow import Flow
from jina.executors import BaseExecutor
from jina.executors.indexers.vector import NumpyIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from tests.integration.incremental_indexing import random_workspace, get_duplicate_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_incremental_indexing_vecindexers(random_workspace):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'inc_vectorindexer.yml'), name='vec_idx'))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(random_workspace / 'vec_idx.bin') as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer.size == num_uniq_docs


def test_incremental_indexing_docindexers(random_workspace):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'inc_docindexer.yml'), shards=1))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(random_workspace / 'doc_idx.bin') as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer.size == num_uniq_docs


def test_incremental_indexing_sequential_indexers(random_workspace):
    total_docs = 20
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=(cur_dir / 'inc_vectorindexer.yml'), shards=1)
         .add(uses=(cur_dir / 'inc_docindexer.yml'), shards=1))

    with f:
        f.index(duplicate_docs[:10])
        f.index(duplicate_docs)

    with BaseExecutor.load(random_workspace / 'vec_idx.bin') as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == num_uniq_docs

    with BaseExecutor.load(random_workspace / 'doc_idx.bin') as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == num_uniq_docs


def test_incremental_indexing_sequential_indexers_with_shards(random_workspace):
    total_docs = 1000
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    num_shards = 4
    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'vectorindexer.yml'),
              uses_before='_unique',
              shards=num_shards,
              separated_workspace=True)
         .add(uses=os.path.join(cur_dir, 'docindexer.yml'),
              uses_before='_unique',
              shards=num_shards,
              separated_workspace=True))
    with f:
        f.index(duplicate_docs[:500])
        f.index(duplicate_docs)

    vect_idx_size = 0
    for shard_idx in range(num_shards):
        save_abspath = (random_workspace / f'vec_idx-{shard_idx + 1}' / 'vec_idx.bin')
        with BaseExecutor.load(save_abspath) as vector_indexer:
            assert isinstance(vector_indexer, NumpyIndexer)
            vect_idx_size += vector_indexer._size
    assert vect_idx_size == num_uniq_docs

    doc_idx_size = 0
    for shard_idx in range(num_shards):
        save_abspath = (random_workspace / f'doc_idx-{shard_idx + 1}' / 'doc_idx.bin')
        with BaseExecutor.load(save_abspath) as doc_indexer:
            assert isinstance(doc_indexer, BinaryPbIndexer)
            doc_idx_size += doc_indexer._size
    assert doc_idx_size == num_uniq_docs


def test_incremental_indexing_parallel_indexers(random_workspace):
    total_docs = 1000
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'inc_vectorindexer.yml'),
              name='inc_vec')
         .add(uses=os.path.join(cur_dir, 'inc_docindexer.yml'),
              name='inc_doc',
              needs=['gateway'])
         .add(uses='_merge', needs=['inc_vec', 'inc_doc']))
    with f:
        f.index(duplicate_docs[:500])
        f.index(duplicate_docs)

    with BaseExecutor.load((random_workspace / 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == num_uniq_docs

    with BaseExecutor.load((random_workspace / 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == num_uniq_docs


def test_incremental_indexing_parallel_indexers_with_shards(random_workspace):
    total_docs = 1000
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    num_shards = 4

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'vectorindexer.yml'),
              uses_before='_unique',
              shards=num_shards,
              name='inc_vec',
              separated_workspace=True)
         .add(uses=os.path.join(cur_dir, 'docindexer.yml'),
              uses_before='_unique',
              shards=num_shards,
              name='inc_doc',
              needs=['gateway'],
              separated_workspace=True)
         .add(uses='_merge',
              needs=['inc_vec', 'inc_doc']))

    with f:
        f.index(duplicate_docs[:500])
        f.index(duplicate_docs)

    vect_idx_size = 0
    for shard_idx in range(num_shards):
        save_abspath = (random_workspace / f'vec_idx-{shard_idx + 1}' / 'vec_idx.bin')
        with BaseExecutor.load(save_abspath) as vector_indexer:
            assert isinstance(vector_indexer, NumpyIndexer)
            vect_idx_size += vector_indexer._size
    assert vect_idx_size == num_uniq_docs

    doc_idx_size = 0
    for shard_idx in range(num_shards):
        save_abspath = (random_workspace / f'doc_idx-{shard_idx + 1}' / 'doc_idx.bin')
        with BaseExecutor.load(save_abspath) as doc_indexer:
            assert isinstance(doc_indexer, BinaryPbIndexer)
            doc_idx_size += doc_indexer._size
    assert doc_idx_size == num_uniq_docs
