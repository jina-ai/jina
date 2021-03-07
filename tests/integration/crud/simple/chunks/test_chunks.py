import os
import random
from pathlib import Path

import numpy as np
import pytest

from jina import Document
from jina.executors.indexers import BaseIndexer
from jina.flow import Flow

from tests import validate_callback

TOP_K = 10


@pytest.fixture
def config(tmpdir):
    random.seed(0)
    np.random.seed(0)
    os.environ['JINA_CRUD_CHUNKS'] = str(tmpdir)
    os.environ['JINA_TOPK'] = str(TOP_K)
    yield
    del os.environ['JINA_CRUD_CHUNKS']
    del os.environ['JINA_TOPK']


d_embedding = np.random.random([9])
c_embedding = np.random.random([9])


def document_generator(start, num_docs, num_chunks):
    chunk_id = num_docs
    for idx in range(start, num_docs):
        with Document() as doc:
            doc.id = idx
            doc.tags['id'] = idx
            doc.text = f'I have {idx} cats'
            doc.embedding = np.random.random([9])
            for chunk_idx in range(num_chunks):
                with Document() as chunk:
                    chunk.id = chunk_id
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


@pytest.mark.parametrize('flow_file', ['flow_vector.yml'])
def test_delete_vector(config, mocker, flow_file):
    num_searches = 10
    num_docs = 10
    num_chunks = 5

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.docs) == num_searches
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with Flow.load_config(flow_file) as index_flow:
        index_flow.index(
            inputs=document_generator(start=0, num_docs=num_docs, num_chunks=num_chunks)
        )
    validate_index_size(num_chunks * num_docs)  # 5 chunks for each of the 10 docs

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            inputs=document_generator(
                start=0, num_docs=num_docs, num_chunks=num_chunks
            ),
            on_done=mock,
        )
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(TOP_K))

    delete_ids = []
    for d in document_generator(start=0, num_docs=num_docs, num_chunks=num_chunks):
        delete_ids.append(d.id)
        for c in d.chunks:
            delete_ids.append(c.id)

    with Flow.load_config(flow_file) as index_flow:
        index_flow.delete(ids=delete_ids)
    validate_index_size(0)

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            inputs=document_generator(
                start=0, num_docs=num_docs, num_chunks=num_chunks
            ),
            on_done=mock,
        )
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))


@pytest.mark.parametrize('flow_file', ['flow_vector.yml'])
def test_update_vector(config, mocker, flow_file):
    num_searches = 10
    num_docs = 10
    num_chunks = 5

    docs_before = list(
        document_generator(start=0, num_docs=num_docs, num_chunks=num_chunks)
    )
    docs_updated = list(
        document_generator(start=10, num_docs=20, num_chunks=num_chunks)
    )
    ids_before = list()
    ids_updated = list()

    def validate_result_factory(has_changed, num_matches):
        def validate_results(resp):
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
        index_flow.index(inputs=docs_before)
    validate_index_size(
        num_chunks * num_docs
    )  # num_docs per all its chunks, 50 in this case

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            inputs=document_generator(
                start=0, num_docs=num_docs, num_chunks=num_chunks
            ),
            on_done=mock,
        )
    mock.assert_called_once()
    validate_callback(
        mock, validate_result_factory(has_changed=False, num_matches=TOP_K)
    )

    with Flow.load_config(flow_file) as index_flow:
        index_flow.update(inputs=docs_updated)
    validate_index_size(
        num_chunks * num_docs
    )  # num_docs per all its chunks, 50 in this case

    mock = mocker.Mock()
    with Flow.load_config(flow_file) as search_flow:
        search_flow.search(
            inputs=document_generator(start=10, num_docs=20, num_chunks=num_chunks),
            on_done=mock,
        )
    mock.assert_called_once()
    validate_callback(
        mock, validate_result_factory(has_changed=True, num_matches=num_docs)
    )
