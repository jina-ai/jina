import os
import pytest
import numpy as np
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb
from jina.executors import BaseExecutor
from jina.executors.compound import CompoundExecutor
from jina.executors.indexers.vector import NumpyIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer

cur_dir = os.path.dirname(os.path.abspath(__file__))


def get_duplicate_docs(num_docs=10):
    result = []
    unique_set = set()
    for idx in range(num_docs):
        doc = jina_pb2.Document()
        content = int(idx/2)
        doc.embedding.CopyFrom(array2pb(np.array([content])))
        doc.text = f'I am doc{content}'
        result.append(doc)
        unique_set.add(content)
    return result, len(unique_set)


def test_incremental_indexing_vecindexers(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'inc_vectorindexer.yml'), shards=1, name='vec_idx'))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == num_uniq_docs

    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


def test_incremental_indexing_docindexers(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'inc_docindexer.yml'), shards=1))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == num_uniq_docs

    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


def test_incremental_indexing_sequential_indexers(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)

    total_docs = 20
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'inc_vectorindexer.yml'), shards=1)
         .add(uses=os.path.join(cur_dir, 'inc_docindexer.yml'), shards=1))

    with f:
        f.index(duplicate_docs[:10])
        f.index(duplicate_docs)

    with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == num_uniq_docs

    with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == num_uniq_docs

    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


def test_incremental_indexing_sequential_indexers_with_shards(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)
    total_docs = 1000
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'inc_vectorindexer.yml'), shards=1)
         .add(uses=os.path.join(cur_dir, 'inc_docindexer.yml'), shards=1))
    with f:
        f.index(duplicate_docs[0: 500])
        # f.index(duplicate_docs)

    # with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
    #     assert isinstance(vector_indexer, NumpyIndexer)
    #     assert vector_indexer._size == num_uniq_docs
    #
    # with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
    #     assert isinstance(doc_indexer, BinaryPbIndexer)
    #     assert doc_indexer._size == num_uniq_docs

    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


@pytest.mark.skip(reason='TDD for incremental indexing')
def test_incremental_indexing_parallel_indexers(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)

    doc0 = jina_pb2.Document()
    doc0.embedding.CopyFrom(array2pb(np.array([0])))
    doc0.text = 'I am doc0'
    doc1 = jina_pb2.Document()
    doc1.embedding.CopyFrom(array2pb(np.array([2])))
    doc1.text = 'I am doc2'
    doc2 = jina_pb2.Document()
    doc2.embedding.CopyFrom(array2pb(np.array([2])))
    doc2.text = 'I am doc2'

    f = Flow(). \
        add(uses=os.path.join(cur_dir, 'vectorindexer.yml'), shards=1, name='vec_idx').add(
        uses=os.path.join(cur_dir, 'docindexer.yml'), shards=1, name='doc_idx',
        needs=['gateway']). \
        add(uses='_merge', needs=['vec_idx', 'doc_idx'], name='join_all')
    with f:
        f.index([doc0, doc1])

    with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == 2

    with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == 2

    with f:
        f.index([doc0, doc2])

    with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == 3

    with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == 3
    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


@pytest.mark.skip(reason='TDD for incremental indexing')
def test_incremental_indexing_parallel_indexers_with_shards(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)

    docs = []
    for i in range(1000):
        doc = jina_pb2.Document()
        doc.embedding.CopyFrom(array2pb(np.array([i])))
        doc.text = f'I am doc{i}'
        docs.append(doc)

    f = Flow(). \
        add(uses=os.path.join(cur_dir, 'vectorindexer.yml'), shards=3, name='vec_idx').add(
        uses=os.path.join(cur_dir, 'docindexer.yml'), shards=3, name='doc_idx',
        needs=['gateway']). \
        add(uses='_merge', needs=['vec_idx', 'doc_idx'], name='join_all')
    with f:
        f.index(docs[0: 900])

    with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == 900

    with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == 900

    with f:
        f.index(docs[0: 950])

    with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer._size == 950

    with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer._size == 950
    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']
