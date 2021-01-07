import os
import random
from pathlib import Path

import numpy as np
import pytest
from jina.executors.indexers import BaseIndexer

from jina import Document
from jina.flow import Flow

random.seed(0)
np.random.seed(0)


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_TOPK_DIR'] = str(tmpdir)
    os.environ['JINA_TOPK'] = '10'
    yield
    del os.environ['JINA_TOPK_DIR']
    del os.environ['JINA_TOPK']


def document_generator(has_content=True, num_docs=10, num_chunks=5):
    for idx in range(num_docs):
        doc = Document()
        doc.id = str(f'{idx}' * 16)
        if has_content:
            doc.tags['id'] = idx
            doc.text = f'I have {idx} cats'
            doc.embedding = np.random.random([9])
        for chunk_idx in range(num_chunks):
            chunk = Document(content=np.array([chunk_idx]))
            doc.chunks.id = str(f'{chunk_idx}' * 16)
            if has_content:
                chunk.tags['id'] = chunk_idx
                chunk.text = f'I have {chunk_idx} chunky cats'
                chunk.embedding = np.random.random([9])
            doc.chunks.append(chunk)
        yield doc


def validate_index_size(num_indexed_docs):
    path = Path(os.environ['JINA_TOPK_DIR'])
    index_files = list(path.glob('*.bin'))
    assert len(index_files) > 0
    for index_file in index_files:
        index = BaseIndexer.load(str(index_file))
        assert index.size == num_indexed_docs


@pytest.mark.parametrize('flow_file, has_content', [
    ['flow.yml', True],
    ['flow_vector.yml', True],
    ['flow.yml', False],
    ['flow_vector.yml', False]
])
def test_delete_vector(config, mocker, flow_file, has_content):
    num_searches = 5
    num_docs = 10
    num_chunks = 5

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == num_searches
            for doc in resp.docs:
                assert len(doc.matches) == num_matches
                assert len(doc.chunks) == num_chunks

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=document_generator(num_docs=num_docs, num_chunks=num_chunks))
    validate_index_size(10)
    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=document_generator(num_docs=num_searches, num_chunks=num_chunks),
            output_fn=validate_result_factory(num_docs))
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(input_fn=document_generator(num_docs=num_docs, num_chunks=num_chunks))
    validate_index_size(0)
    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(input_fn=document_generator(num_docs=num_searches, num_chunks=num_chunks),
            output_fn=validate_result_factory(0))
    mock.assert_called_once()


