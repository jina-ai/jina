import os

from jina.clients.python import PyClient
from jina.executors import BaseExecutor
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.executors.indexers.vector import NumpyIndexer
from jina.flow import Flow
from tests.integration.incremental_indexing import random_workspace, get_duplicate_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))

# don't remove this line, otherwise auto-code-format will remove `random_workspace`
print(random_workspace)


def test_incremental_indexing_sequential_indexers(random_workspace):
    total_docs = 20
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'uniq_vectorindexer.yml'))
         .add(uses=os.path.join(cur_dir, 'uniq_docindexer.yml')))

    PyClient.check_input(duplicate_docs[:10])
    PyClient.check_input(duplicate_docs)

    with f:
        f.index(duplicate_docs[:10])

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(random_workspace / 'vec_idx.bin') as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == num_uniq_docs

    with BaseExecutor.load(random_workspace / 'doc_idx.bin') as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == num_uniq_docs


def test_incremental_indexing_parallel_indexers(random_workspace):
    total_docs = 1000
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'uniq_vectorindexer.yml'),
              name='inc_vec')
         .add(uses=os.path.join(cur_dir, 'uniq_docindexer.yml'),
              name='inc_doc',
              needs=['gateway'])
         .add(needs=['inc_vec', 'inc_doc']))
    with f:
        f.index(duplicate_docs[:500])

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load((random_workspace / 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == num_uniq_docs

    with BaseExecutor.load((random_workspace / 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == num_uniq_docs


def test_incremental_indexing_sequential_indexers_with_shards(random_workspace):
    total_docs = 1000
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    num_shards = 4
    # can't use plain _unique in uses_before because workspace will conflict with other
    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'vectorindexer.yml'),
              uses_before=os.path.join(cur_dir, '_unique_vec.yml'),
              shards=num_shards,
              separated_workspace=True)
         .add(uses=os.path.join(cur_dir, 'docindexer.yml'),
              uses_before=os.path.join(cur_dir, '_unique_doc.yml'),
              shards=num_shards,
              separated_workspace=True))

    with f:
        f.index(duplicate_docs[:500])

    with f:
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


def test_incremental_indexing_parallel_indexers_with_shards(random_workspace):
    total_docs = 1000
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    num_shards = 4

    # can't use plain _unique in uses_before because workspace will conflict with other
    f = (Flow()
        .add(uses=os.path.join(cur_dir, 'vectorindexer.yml'),
             uses_before=os.path.join(cur_dir, '_unique_vec.yml'),
             shards=num_shards,
             name='inc_vec',
             separated_workspace=True)
        .add(uses=os.path.join(cur_dir, 'docindexer.yml'),
             uses_before=os.path.join(cur_dir, '_unique_doc.yml'),
             shards=num_shards,
             name='inc_doc',
             needs=['gateway'],
             separated_workspace=True)
        .add(
        needs=['inc_vec', 'inc_doc']))

    with f:
        f.index(duplicate_docs[:500])

    with f:
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
