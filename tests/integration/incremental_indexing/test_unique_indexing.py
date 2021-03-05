import os

import pytest

from jina.executors import BaseExecutor
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.executors.indexers.vector import NumpyIndexer
from jina.flow import Flow
from tests.integration.incremental_indexing import get_duplicate_docs, random_workspace

cur_dir = os.path.dirname(os.path.abspath(__file__))

# don't remove this line, otherwise auto-code-format will remove `random_workspace`
print(random_workspace)


@pytest.mark.parametrize('restful', [False, True])
def test_unique_indexing_vecindexers(random_workspace, restful):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = Flow(restful=restful).add(
        uses=os.path.join(cur_dir, 'uniq_vectorindexer.yml'), name='vec_idx'
    )

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(
        (random_workspace / 'inc_vecindexer' / 'vec_idx.bin')
    ) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer.size == num_uniq_docs


@pytest.mark.parametrize('restful', [False, True])
def test_unique_indexing_docindexers(random_workspace, restful):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = Flow(restful=restful).add(
        uses=os.path.join(cur_dir, 'uniq_docindexer.yml'), shards=1
    )

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(
        (random_workspace / 'inc_docindexer' / 'doc_idx.bin')
    ) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer.size == num_uniq_docs


@pytest.mark.parametrize('restful', [False, True])
def test_unique_indexing_vecindexers_before(random_workspace, restful):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    # can't use plain _unique because workspace will conflict with other tests
    f = Flow(restful=restful).add(
        uses=os.path.join(cur_dir, 'vectorindexer.yml'),
        uses_before=os.path.join(cur_dir, '_unique_vec.yml'),
    )

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load((random_workspace / 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer.size == num_uniq_docs


@pytest.mark.parametrize('restful', [False, True])
def test_unique_indexing_docindexers_before(random_workspace, restful):
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    # can't use plain _unique because workspace will conflict with other tests
    f = Flow(restful=restful).add(
        uses=os.path.join(cur_dir, 'docindexer.yml'),
        uses_before=os.path.join(cur_dir, '_unique_doc.yml'),
    )

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load((random_workspace / 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer.size == num_uniq_docs
