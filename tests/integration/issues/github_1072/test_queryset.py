import os

import numpy as np
import pytest

from jina import QueryLang
from jina.drivers.querylang.filter import FilterQL
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def random_workspace(tmpdir):
    os.environ['JINA_TEST_QUERYSET_WORKSPACE'] = str(tmpdir)
    yield tmpdir
    del os.environ['JINA_TEST_QUERYSET_WORKSPACE']


def test_queryset_with_struct(random_workspace):
    total_docs = 4
    docs = []
    for doc_id in range(total_docs):
        doc = jina_pb2.DocumentProto()
        doc.text = f'I am doc{doc_id}'
        NdArray(doc.embedding).value = np.array([doc_id])
        doc.tags['label'] = f'label{doc_id % 2 + 1}'
        docs.append(doc)

    f = (Flow()
         .add(uses='- !FilterQL | {lookups: {tags__label__in: [label1, label2]}, traversal_paths: [r]}'))

    def validate_all_docs(resp):
        assert len(resp.docs) == total_docs

    def validate_label2_docs(resp):
        assert len(resp.docs) == total_docs / 2

    with f:
        # keep all the docs
        f.index(docs, output_fn=validate_all_docs, callback_on='body')
        # keep only the docs with label2
        qs = QueryLang(FilterQL(priority=1, lookups={'tags__label': 'label2'}, traversal_paths=['r']))
        f.index(docs, queryset=qs, output_fn=validate_label2_docs, callback_on='body')