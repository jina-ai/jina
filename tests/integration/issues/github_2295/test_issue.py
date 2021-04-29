import os
from typing import Iterable, List

import pytest

from jina.drivers.search import KVSearchDriver
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.flow import Flow
from jina import Document, DocumentArray

from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


class SearchDocIndexer(BinaryPbIndexer):
    def query(self, jina_id: str = None, mongo_ids: List[str] = None):
        return super().query([jina_id])[0]  # serialized document

    def post_init(self):
        super().post_init()
        # key to have user workaround https://github.com/jina-ai/jina/issues/2295.
        # Underlying problem in https://github.com/jina-ai/jina/issues/2299
        self.name = 'doc_idx_file'


class SearchDocDriver(KVSearchDriver):
    def _apply_all(
        self, doc_sequences: Iterable['DocumentArray'], *args, **kwargs
    ) -> None:
        for docs in doc_sequences:
            for idx, doc in enumerate(docs):
                serialized_doc = self.exec_fn(jina_id=doc.id)
                if serialized_doc:
                    doc.MergeFrom(Document(serialized_doc))  # merge!


@pytest.fixture
def test_workspace(tmpdir):
    os.environ['TEST_2295_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['TEST_2295_WORKSPACE']


def test_issue_2295(test_workspace, mocker):
    # This tests the proposed workaround to user in 2295, once https://github.com/jina-ai/jina/issues/2299 this test
    # can be removed
    def validate_response(resp):
        assert resp.search.docs[0].id == 'id'
        assert resp.search.docs[0].text == 'text'

    index_set = DocumentArray([Document(id='id', text='text')])
    query_set = DocumentArray([Document(id='id')])

    with Flow.load_config(os.path.join(cur_dir, 'flow_index.yml')) as f:
        f.index(inputs=index_set)

    mock_on_done = mocker.Mock()

    with Flow.load_config(os.path.join(cur_dir, 'flow_query.yml')) as f:
        f.search(inputs=query_set, on_done=mock_on_done)

    validate_callback(mock_on_done, validate_response)
