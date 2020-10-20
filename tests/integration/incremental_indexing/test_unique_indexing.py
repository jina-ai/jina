import os

from jina.executors import BaseExecutor
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.executors.indexers.vector import NumpyIndexer
from jina.flow import Flow
from tests.integration.incremental_indexing import random_workspace, get_duplicate_docs


cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_incremental_indexing_vecindexers(random_workspace):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'uniq_vectorindexer.yml'), name='vec_idx'))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load((random_workspace / 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer.size == num_uniq_docs


def test_incremental_indexing_docindexers(random_workspace):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'uniq_docindexer.yml'), shards=1))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load((random_workspace / 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer.size == num_uniq_docs
