import os
from pathlib import Path

import numpy as np
import pytest

from jina import Document
from jina.executors.indexers import BaseIndexer
from jina.flow import Flow


def random_docs_only_tags(nr_docs, start=0):
    for j in range(start, nr_docs + start):
        d = Document()
        d.tags['id'] = j
        d.tags['something'] = f'abcdef {j}'
        yield d


def validate_index_size(num_indexed_docs, expected_indices):
    path = Path(os.environ['JINA_CORRUPTED_DOCS_TEST_DIR'])
    index_files = list(path.glob('*.bin'))
    assert len(index_files) == expected_indices
    for index_file in index_files:
        index = BaseIndexer.load(str(index_file))
        assert index.size == num_indexed_docs


TOPK = 5
NR_DOCS_INDEX = 20
NUMBER_OF_SEARCHES = 5
# since there is no content or embedding to match on
EXPECTED_ONLY_TAGS_RESULTS = 0


def config_environ(path):
    os.environ['JINA_CORRUPTED_DOCS_TEST_DIR'] = str(path)
    os.environ['JINA_TOPK'] = str(TOPK)


def test_only_tags(tmp_path, mocker):
    config_environ(path=tmp_path)
    flow_file = 'flow.yml'
    docs = list(random_docs_only_tags(NR_DOCS_INDEX))
    docs_update = list(random_docs_only_tags(NR_DOCS_INDEX, start=len(docs) + 1))
    all_docs_indexed = docs.copy()
    all_docs_indexed.extend(docs_update)
    docs_search = list(random_docs_only_tags(NUMBER_OF_SEARCHES, start=len(docs) + len(docs_update) + 1))
    f = Flow.load_config(flow_file)

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with f:
        f.index(input_fn=docs)
    validate_index_size(NR_DOCS_INDEX, expected_indices=1)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(EXPECTED_ONLY_TAGS_RESULTS))
    mock.assert_called_once()

    # this won't increase the index size as the ids are new
    with f:
        f.update(input_fn=docs_update)
    validate_index_size(NR_DOCS_INDEX, expected_indices=1)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(EXPECTED_ONLY_TAGS_RESULTS))
    mock.assert_called_once()

    with f:
        f.delete(input_fn=all_docs_indexed)
    # only stored in KV
    validate_index_size(NR_DOCS_INDEX, expected_indices=1)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(0))
    mock.assert_called_once()


np.random.seed(0)

EMBEDDING_SHAPE = (7)


def random_docs_only_embedding(nr_docs, text=False, mime_type='plain/text', start=0):
    for i in range(start, nr_docs + start):
        d = Document()
        if text:
            d.text = 'some text here'
        d.embedding = np.random.random(EMBEDDING_SHAPE)
        d.mime_type = mime_type
        yield d


@pytest.mark.parametrize('mime_type',
                         ['text/plain', 'image/jpeg', 'text/x-python'])
def test_only_embedding_and_mime_type(tmp_path, mocker, mime_type):
    config_environ(path=tmp_path)
    flow_file = 'flow.yml'
    docs = list(random_docs_only_embedding(NR_DOCS_INDEX, mime_type=mime_type))
    docs_update = list(random_docs_only_embedding(NR_DOCS_INDEX, mime_type=mime_type, start=len(docs) + 1))
    all_docs_indexed = docs.copy()
    all_docs_indexed.extend(docs_update)
    docs_search = list(
        random_docs_only_embedding(NUMBER_OF_SEARCHES, mime_type=mime_type, start=len(docs) + len(docs_update) + 1))
    f = Flow.load_config(flow_file)

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches
                for m in doc.matches:
                    assert m.mime_type == mime_type

        return validate_results

    with f:
        f.index(input_fn=docs)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(TOPK))
    mock.assert_called_once()

    # this won't increase the index size as the ids are new
    with f:
        f.update(input_fn=docs_update)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(TOPK))
    mock.assert_called_once()

    with f:
        f.delete(input_fn=all_docs_indexed)
    validate_index_size(0, expected_indices=2)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(0))
    mock.assert_called_once()


def test_malformed(tmp_path, mocker):
    """we assign text to .text but the image mime type"""
    config_environ(path=tmp_path)
    flow_file = 'flow-parallel.yml'
    flow_query_file = 'flow.yml'
    mime_type = 'image/jpeg'
    docs = list(random_docs_only_embedding(NR_DOCS_INDEX, text=True, mime_type=mime_type))
    docs_update = list(random_docs_only_embedding(NR_DOCS_INDEX, text=True, mime_type=mime_type, start=len(docs) + 1))
    all_docs_indexed = docs.copy()
    all_docs_indexed.extend(docs_update)
    docs_search = list(
        random_docs_only_embedding(NUMBER_OF_SEARCHES, text=True, mime_type=mime_type, start=len(docs) + len(docs_update) + 1))
    f_index = Flow.load_config(flow_file)
    f_query = Flow.load_config(flow_query_file)

    def validate_result_factory(num_matches):
        def validate_results(resp):
            mock()
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches
                for m in doc.matches:
                    assert m.mime_type == mime_type

        return validate_results

    with f_index:
        f_index.index(input_fn=docs)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(input_fn=docs_search,
                 output_fn=validate_result_factory(TOPK))
    mock.assert_called_once()

    # this won't increase the index size as the ids are new
    with f_index:
        f_index.update(input_fn=docs_update)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(input_fn=docs_search,
                 output_fn=validate_result_factory(TOPK))
    mock.assert_called_once()

    with f_index:
        f_index.delete(input_fn=all_docs_indexed)
    validate_index_size(0, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(input_fn=docs_search,
                 output_fn=validate_result_factory(0))
    mock.assert_called_once()