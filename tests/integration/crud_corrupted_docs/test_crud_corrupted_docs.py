import os
from pathlib import Path

import numpy as np
import pytest

from jina import Document
from jina.executors.indexers import BaseIndexer
from jina.flow import Flow

from tests import validate_callback


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
    docs_search = list(
        random_docs_only_tags(
            NUMBER_OF_SEARCHES, start=len(docs) + len(docs_update) + 1
        )
    )
    f = Flow.load_config(flow_file)

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with f:
        f.index(inputs=docs)
    validate_index_size(NR_DOCS_INDEX, expected_indices=1)

    mock = mocker.Mock()
    with f:
        f.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(EXPECTED_ONLY_TAGS_RESULTS))

    # this won't increase the index size as the ids are new
    with f:
        f.update(inputs=docs_update)
    validate_index_size(NR_DOCS_INDEX, expected_indices=1)

    mock = mocker.Mock()
    with f:
        f.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(EXPECTED_ONLY_TAGS_RESULTS))

    mock = mocker.Mock()
    with f:
        f.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))


np.random.seed(0)

EMBEDDING_SHAPE = 7

ORIGINAL_MIME_TYPE = 'image/jpeg'


def random_docs_content_field(nr_docs, field, start=0):
    for i in range(start, nr_docs + start):
        with Document() as d:
            d.id = i
            d.embedding = np.random.random(EMBEDDING_SHAPE)
            d.mime_type = ORIGINAL_MIME_TYPE
            if field == 'content':
                # mime type will be overridden because it's `str`
                d.content = 'I am text'
            elif field == 'buffer':
                # mime type will be preserved and ignored
                d.buffer = b'hidden text in bytes'
            elif field == 'blob':
                # mime type is ignored and preserved
                d.blob = np.random.random(EMBEDDING_SHAPE)

        yield d


@pytest.mark.parametrize('field', ['content', 'buffer', 'blob'])
def test_only_embedding_and_mime_type(tmp_path, mocker, field):
    config_environ(path=tmp_path)
    flow_file = 'flow.yml'
    docs = list(random_docs_content_field(NR_DOCS_INDEX, field=field))
    docs_update = list(
        random_docs_content_field(NR_DOCS_INDEX, field=field, start=len(docs) + 1)
    )
    all_docs_indexed = docs.copy()
    all_docs_indexed.extend(docs_update)
    docs_search = list(
        random_docs_content_field(
            NUMBER_OF_SEARCHES, field=field, start=len(docs) + len(docs_update) + 1
        )
    )
    f = Flow.load_config(flow_file)

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches
                for m in doc.matches:
                    if field == 'content':
                        assert m.content == 'I am text'
                        assert m.mime_type == 'text/plain'
                    elif field == 'buffer':
                        # mime type will be preserved from when we set it to the Doc
                        assert m.buffer == b'hidden text in bytes'
                        assert m.mime_type == ORIGINAL_MIME_TYPE
                    elif field == 'blob':
                        assert m.blob.shape == (EMBEDDING_SHAPE,)
                        assert m.mime_type == ORIGINAL_MIME_TYPE

        return validate_results

    with f:
        f.index(inputs=docs)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f:
        f.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(TOPK))

    # this won't increase the index size as the ids are new
    with f:
        f.update(inputs=docs_update)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f:
        f.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(TOPK))

    with f:
        f.delete(ids=[d.id for d in all_docs_indexed])
    validate_index_size(0, expected_indices=2)

    mock = mocker.Mock()
    with f:
        f.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))


def random_docs_image_mime_text_content(nr_docs, start=0):
    for i in range(start, nr_docs + start):
        with Document() as d:
            d.embedding = np.random.random(EMBEDDING_SHAPE)
            d.mime_type = 'image/jpeg'
            d.text = f'document {i}'
        yield d


def test_wrong_mime_type(tmp_path, mocker):
    """we assign text to .text, 'image/jpeg' to .mime_type"""
    config_environ(path=tmp_path)
    flow_file = 'flow-parallel.yml'
    flow_query_file = 'flow.yml'
    docs = list(random_docs_image_mime_text_content(NR_DOCS_INDEX))
    docs_update = list(
        random_docs_image_mime_text_content(NR_DOCS_INDEX, start=len(docs) + 1)
    )
    all_docs_indexed = docs.copy()
    all_docs_indexed.extend(docs_update)
    docs_search = list(
        random_docs_image_mime_text_content(
            NUMBER_OF_SEARCHES, start=len(docs) + len(docs_update) + 1
        )
    )
    f_index = Flow.load_config(flow_file)
    f_query = Flow.load_config(flow_query_file)

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches
                for m in doc.matches:
                    assert m.mime_type == 'text/plain'

        return validate_results

    with f_index:
        f_index.index(inputs=docs)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(TOPK))

    # this won't increase the index size as the ids are new
    with f_index:
        f_index.update(inputs=docs_update)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(TOPK))

    with f_index:
        f_index.delete(ids=[d.id for d in all_docs_indexed])
    validate_index_size(0, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))


START_SHAPE = 7
INDEX2_SHAPE = 6
UPDATE_SHAPE = 7


def random_docs_with_shapes(nr_docs, emb_shape, start=0):
    for i in range(start, nr_docs + start):
        with Document() as d:
            d.id = i
            d.embedding = np.random.random(emb_shape)
        yield d


def test_dimensionality_search_wrong(tmp_path, mocker):
    """will fail because search docs have diff shape in embedding"""
    config_environ(path=tmp_path)
    flow_file = 'flow.yml'
    flow_query_file = 'flow.yml'
    docs = list(random_docs_with_shapes(NR_DOCS_INDEX, START_SHAPE))
    docs_update = list(
        random_docs_with_shapes(NR_DOCS_INDEX, INDEX2_SHAPE, start=len(docs) + 1)
    )
    all_docs_indexed = docs.copy()
    all_docs_indexed.extend(docs_update)
    docs_search = list(
        random_docs_with_shapes(
            NUMBER_OF_SEARCHES, INDEX2_SHAPE, start=len(docs) + len(docs_update) + 1
        )
    )
    f_index = Flow.load_config(flow_file)
    f_query = Flow.load_config(flow_query_file)

    def validate_result_factory(num_matches):
        def validate_results(resp):
            assert len(resp.docs) == NUMBER_OF_SEARCHES
            for doc in resp.docs:
                assert len(doc.matches) == num_matches

        return validate_results

    with f_index:
        f_index.index(inputs=docs)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(
            inputs=docs_search,
            # 0 because search docs have wrong shape
            on_done=mock,
        )
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))

    # this won't increase the index size as the ids are new
    with f_index:
        f_index.update(inputs=docs_update)
    validate_index_size(NR_DOCS_INDEX, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(
            inputs=docs_search,
            # 0 because search docs have wrong shape
            on_done=mock,
        )
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))

    with f_index:
        f_index.delete(ids=[d.id for d in all_docs_indexed])
    validate_index_size(0, expected_indices=2)

    mock = mocker.Mock()
    with f_query:
        f_query.search(inputs=docs_search, on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate_result_factory(0))
