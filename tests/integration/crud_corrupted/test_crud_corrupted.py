import os
from pathlib import Path

from jina import Document
from jina.executors.indexers import BaseIndexer
from jina.flow import Flow


def random_docs_only_tags(nr_docs, start=0):
    for j in range(start, nr_docs + start):
        d = Document()
        d.tags['id'] = j
        d.tags['something'] = f'abcdef {j}'
        yield d


def validate_index_size(num_indexed_docs):
    path = Path(os.environ['JINA_CORRUPTED_DOCS_TEST_DIR'])
    index_files = list(path.glob('*.bin'))
    assert len(index_files) > 0
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
    validate_index_size(NR_DOCS_INDEX)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(EXPECTED_ONLY_TAGS_RESULTS))
    mock.assert_called_once()

    # this won't increase the index size as the ids are new
    with f:
        f.update(input_fn=docs_update)
    validate_index_size(NR_DOCS_INDEX)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(EXPECTED_ONLY_TAGS_RESULTS))
    mock.assert_called_once()

    with f:
        f.delete(input_fn=all_docs_indexed)
    validate_index_size(0)

    mock = mocker.Mock()
    with f:
        f.search(input_fn=docs_search,
                 output_fn=validate_result_factory(0))
    mock.assert_called_once()
