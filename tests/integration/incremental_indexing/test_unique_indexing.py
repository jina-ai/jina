import os

import numpy as np

from jina.drivers.helper import array2pb
from jina.executors import BaseExecutor
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.executors.indexers.vector import NumpyIndexer
from jina.flow import Flow
from jina.proto import jina_pb2

cur_dir = os.path.dirname(os.path.abspath(__file__))


def get_duplicate_docs(num_docs=10):
    result = []
    unique_set = set()
    for idx in range(num_docs):
        doc = jina_pb2.Document()
        content = int(idx / 2)
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
         .add(uses=os.path.join(cur_dir, 'uniq_vectorindexer.yml'), name='vec_idx'))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(os.path.join(tmpdir, 'vec_idx.bin')) as vector_indexer:
        assert isinstance(vector_indexer, NumpyIndexer)
        assert vector_indexer.size == num_uniq_docs

    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']


def test_incremental_indexing_docindexers(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)
    total_docs = 10
    duplicate_docs, num_uniq_docs = get_duplicate_docs(num_docs=total_docs)

    f = (Flow()
         .add(uses=os.path.join(cur_dir, 'uniq_docindexer.yml'), shards=1))

    with f:
        f.index(duplicate_docs)

    with BaseExecutor.load(os.path.join(tmpdir, 'doc_idx.bin')) as doc_indexer:
        assert isinstance(doc_indexer, BinaryPbIndexer)
        assert doc_indexer.size == num_uniq_docs

    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']