import os

import numpy as np
import pytest

from jina import QueryLang
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray

from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def random_workspace(tmpdir):
    os.environ['JINA_TEST_QUERYSET_WORKSPACE'] = str(tmpdir)
    yield tmpdir
    del os.environ['JINA_TEST_QUERYSET_WORKSPACE']


def test_queryset_with_struct(random_workspace, mocker):
    total_docs = 4
    docs = []
    for doc_id in range(total_docs):
        doc = jina_pb2.DocumentProto()
        doc.text = f'I am doc{doc_id}'
        NdArray(doc.embedding).value = np.array([doc_id])
        doc.tags['label'] = f'label{doc_id % 2 + 1}'
        docs.append(doc)

    f = Flow().add(
        uses='- !FilterQL | {lookups: {tags__label__in: [label1, label2]}, traversal_paths: [r]}'
    )

    def validate_all_docs(resp):
        assert len(resp.docs) == total_docs

    def validate_label2_docs(resp):
        assert len(resp.docs) == total_docs / 2

    mock1 = mocker.Mock()
    mock2 = mocker.Mock()
    with f:
        # keep all the docs
        f.index(docs, on_done=mock1)
        # keep only the docs with label2
        qs = QueryLang(
            {
                'name': 'FilterQL',
                'priority': 1,
                'parameters': {
                    'lookups': {'tags__label': 'label2'},
                    'traversal_paths': ['r'],
                },
            }
        )
        f.index(docs, queryset=qs, on_done=mock2)

    mock1.assert_called_once()
    validate_callback(mock1, validate_all_docs)
    mock2.assert_called_once()
    validate_callback(mock2, validate_label2_docs)
