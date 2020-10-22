import os

import numpy as np
import pytest
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb


@pytest.fixture
def config(tmpdir):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ['JINA_TOPK_DIR'] = str(tmpdir)
    os.environ['JINA_NDOCS'] = '3'
    os.environ['JINA_TOPK'] = '9'
    os.environ['JINA_TOPK_OVERRIDE'] = '11'


def random_docs(num_docs, embed_dim=10, jitter=1):
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.tags['id'] = j
        d.text = b'hello'
        d.embedding.CopyFrom(array2pb(np.random.random([embed_dim + np.random.randint(0, jitter)])))
        yield d


def validate_results(resp):
    n = []
    for d in resp.search.docs:
        n.append([k.id for k in d.matches])
    n = np.array(n)

    np.testing.assert_equal(n.shape[0], int(os.environ['JINA_NDOCS']))
    np.testing.assert_equal(n.shape[1], int(os.environ['JINA_TOPK']))


def test_topk(config):
    with Flow().load_config('flow.yml') as index_flow:
        index_flow.index(input_fn=random_docs(100))
    with Flow().load_config('flow.yml') as index_flow:
        index_flow.search(input_fn=random_docs(int(os.environ['JINA_NDOCS'])), 
                          output_fn=validate_results)


def validate_override_results(resp):
    n = []
    for d in resp.search.docs:
        n.append([k.id for k in d.matches])
    n = np.array(n)

    np.testing.assert_equal(n.shape[0], int(os.environ['JINA_NDOCS']))
    np.testing.assert_equal(n.shape[1], int(os.environ['JINA_TOPK_OVERRIDE']))


def test_topk_override(config):
    # Making queryset
    top_k_queryset = jina_pb2.QueryLang()
    top_k_queryset.name = 'VectorSearchDriver'
    top_k_queryset.priority = 1
    top_k_queryset.parameters['top_k'] = os.environ['JINA_TOPK_OVERRIDE']

    with Flow().load_config('flow.yml') as index_flow:
        index_flow.index(input_fn=random_docs(100))
    with Flow().load_config('flow.yml') as index_flow:
        index_flow.search(input_fn=random_docs(int(os.environ['JINA_NDOCS'])), 
                          output_fn=validate_override_results, queryset=top_k_queryset)

