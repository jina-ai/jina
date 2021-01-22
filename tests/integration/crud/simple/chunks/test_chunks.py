import os
import random
from itertools import chain
from pathlib import Path

import numpy as np
import pytest
from jina.executors.indexers import BaseIndexer

from jina import Document
from jina.flow import Flow

TOP_K = 10

@pytest.fixture
def config(tmpdir):
    random.seed(0)
    np.random.seed(0)
    os.environ['JINA_CRUD_CHUNKS'] = str(tmpdir)
    os.environ['JINA_TOPK'] = '10'
    yield
    del os.environ['JINA_CRUD_CHUNKS']
    del os.environ['JINA_TOPK']


d_embedding = np.random.random([9])
c_embedding = np.random.random([9])


def document_generator(content_same, start, num_docs, num_chunks):
    chunk_id = num_docs
    for idx in range(start, num_docs):
        with Document() as doc:
            doc.id = idx
            if content_same:
                doc.tags['id'] = idx
                doc.text = 'I have cats'
                doc.embedding = d_embedding
            else:
                doc.text = f'I have {idx} cats'
                doc.embedding = np.random.random([9])
            for chunk_idx in range(num_chunks):
                with Document() as chunk:
                    chunk.id = chunk_id
                    if content_same:
                        chunk.tags['id'] = chunk_idx
                        chunk.text = 'I have chunky cats'
                        chunk.embedding = c_embedding
                    else:
                        chunk.tags['id'] = chunk_idx
                        chunk.text = f'I have {chunk_idx} chunky cats'
                        chunk.embedding = np.random.random([9])
                chunk_id += 1
                doc.chunks.append(chunk)
        yield doc


def validate_index_size(num_indexed_docs):
    path = Path(os.environ['JINA_CRUD_CHUNKS'])
    index_files = list(path.glob('*.bin'))
    assert len(index_files) > 0
    for index_file in index_files:
        index = BaseIndexer.load(str(index_file))
        assert index.size == num_indexed_docs


@pytest.mark.parametrize('flow_file, content_same', [
    ['flow_vector.yml', False],
    ['flow_vector.yml', True]
])
def test_delete_vector(config, mocker, flow_file, content_same):
    num_searches = 10
    num_docs = 10
    num_chunks = 5

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == num_searches
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(
            input_fn=document_generator(content_same=content_same, start=0, num_docs=num_docs, num_chunks=num_chunks))
    validate_index_size(50) #5 chunks for each of the 10 docs

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            input_fn=document_generator(content_same=content_same, start=0, num_docs=num_docs, num_chunks=num_chunks),
            on_done=validate_result_factory(TOP_K))
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(
            input_fn=document_generator(content_same=content_same, start=0, num_docs=num_docs, num_chunks=num_chunks))
    validate_index_size(0)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            input_fn=document_generator(content_same=content_same, start=0, num_docs=num_docs, num_chunks=num_chunks),
            on_done=validate_result_factory(0))
    mock.assert_called_once()


@pytest.mark.parametrize('flow_file, content_same', [
    ['flow_vector.yml', False],
    ['flow_vector.yml', True]
])
def test_update_vector(config, mocker, flow_file, content_same):
    num_searches = 10
    num_docs = 10
    num_chunks = 5
    num_matches = num_docs * num_chunks

    docs_before = list(document_generator(content_same=content_same, start=0, num_docs=num_docs, num_chunks=num_chunks))
    docs_updated = list(document_generator(content_same=content_same, start=10, num_docs=20, num_chunks=num_chunks))
    ids_before = list()
    ids_updated = list()

    def validate_result_factory(has_changed, num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == num_searches
            for d in docs_before:
                ids_before.append(d.id)
            for d in docs_updated:
                ids_updated.append(d.id)
            for doc in resp.docs:
                assert len(doc.matches) == num_matches
                if has_changed:
                    assert doc.id in ids_updated
                    assert doc.id not in ids_before
                else:
                    assert doc.id in ids_before
                    assert doc.id not in ids_updated
        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(input_fn=docs_before)
    validate_index_size(num_matches) #num_docs per all its chunks, 50 in this case

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            input_fn=document_generator(content_same=content_same, start=0, num_docs=num_docs, num_chunks=num_chunks),
            on_done=validate_result_factory(has_changed=False, num_matches=TOP_K))
    mock.assert_called_once()

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(input_fn=docs_updated)
    validate_index_size(num_matches) #num_docs per all its chunks, 50 in this case

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            input_fn=document_generator(content_same=content_same, start=10, num_docs=20, num_chunks=num_chunks),
            on_done=validate_result_factory(has_changed=True, num_matches=num_docs))
    mock.assert_called_once()


