import os
import numpy as np
import pytest

from jina import Flow, Document

callback_was_called = False


def get_index_flow():
    num_shards = 2
    f = Flow() \
        .add(
        uses='vectorindexer.yml',
        shards=num_shards,
        separated_workspace=True,
    )
    return f


def get_search_flow():
    num_shards = 2
    f = Flow(read_only=True) \
        .add(
        uses='vectorindexer.yml',
        shards=num_shards,
        separated_workspace=True,
        uses_after='_merge_matches',
        polling='all',
        timeout_ready='-1'
    )
    return f


# required because we don't know the order of the pod returning
# and, when the test failed, we still some time didn't see the error
@pytest.mark.parametrize('execution_number', range(10))
def test_sharding_empty_index(tmpdir, execution_number, mocker):
    os.environ['JINA_TEST_1229_WORKSPACE'] = os.path.abspath(tmpdir)

    f = get_index_flow()

    num_docs = 1
    data = []
    for i in range(num_docs):
        with Document() as doc:
            doc.content = f'data {i}'
            doc.embedding = np.array([i])
            data.append(doc)

    with f:
        f.index(data)

    f = get_search_flow()

    num_query = 10
    query = []
    for i in range(num_query):
        with Document() as doc:
            doc.content = f'query {i}'
            doc.embedding = np.array([i])
            query.append(doc)

    def callback(result):
        mock()
        assert len(result.docs) == num_query
        for d in result.docs:
            assert len(list(d.matches)) == num_docs

    mock = mocker.Mock()
    with f:
        f.search(query, on_done=callback)

    mock.assert_called_once()
