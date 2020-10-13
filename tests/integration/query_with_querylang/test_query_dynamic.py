import os
import numpy as np

from jina.proto import jina_pb2
from jina.drivers.helper import array2pb
from jina.executors import BaseExecutor
from jina.executors.indexers.vector import NumpyIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_querylang_index(tmpdir):
    os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE'] = str(tmpdir)

    total_docs = 4
    docs = []
    for doc_id in range(total_docs):
        doc = jina_pb2.Document()
        doc.text = f'I am doc{doc_id}'
        doc.embedding.CopyFrom(array2pb(np.array([doc_id])))
        doc.tags['label'] = f'label{doc_id%2 + 1}'
        docs.append(doc)

    index_flow = (Flow()
         .add(uses=os.path.join(cur_dir, 'vec_indexer_1.yml'),
              name='idx_1')
         .add(uses=os.path.join(cur_dir, 'vec_indexer_2.yml'),
              needs=['gateway'],
              name='idx_2')
         .join(needs=['idx_1', 'idx_2']))

    with index_flow:
        index_flow.index(docs, output_fn=print)

    for indexer_id in range(2):
        with BaseExecutor.load(os.path.join(tmpdir, f'vec_{indexer_id+1}.bin')) as vector_indexer:
            assert isinstance(vector_indexer, NumpyIndexer)
            assert vector_indexer._size == 2

        with BaseExecutor.load(os.path.join(tmpdir, f'doc_{indexer_id + 1}.bin')) as vector_indexer:
            assert isinstance(vector_indexer, BinaryPbIndexer)
            assert vector_indexer._size == 2

    query_flow = (Flow()
                  .add(uses=os.path.join(cur_dir, 'vec_indexer_1.yml'),
                       needs=['gateway', ],
                       name='idx_1')
                  .add(uses=os.path.join(cur_dir, 'vec_indexer_2.yml'),
                       needs=['gateway', ],
                       name='idx_2')
                  .add(uses=os.path.join(cur_dir, 'join_matches.yml'),
                       needs=['idx_1', 'idx_2'])
                  .add(uses='- !FilterQL | {lookups: {tags__label__in: [label1, label2]}, traversal_paths: [m]}'))

    def validate_both_labels(resp):
        for doc in resp.docs:
            assert len(doc.matches) == 4

    def validate_only_label2(resp):
        for doc in resp.docs:
            assert len(doc.matches) == 2

    with query_flow:
        # match all docs
        query_flow.search(docs[:1], output_fn=validate_both_labels, callback_on_body=True)

        # match only docs with label1
        qs = jina_pb2.QueryLang(name='FilterQL', priority=100)
        qs.parameters['lookups'] = {'tags__label': 'label1'}
        qs.parameters['traversal_paths'] = ['m']
        query_flow.search(docs[:1], queryset=qs, output_fn=validate_only_label2, callback_on_body=True)

    del os.environ['JINA_TEST_INCREMENTAL_INDEX_WORKSPACE']
