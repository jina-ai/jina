import pytest

from jina import Document, DocumentArray, Executor, Flow, requests
from tests import validate_callback


@pytest.fixture()
def test_docs():
    return DocumentArray([Document(id='1')])


def test_different_responses(test_docs, mocker):
    def assert_response(response):
        assert len(response.data.docs) == 1
        assert response.data.docs[0].id == '1'

    class MyExecutor(Executor):
        @requests(on='/return_docs')
        def return_docs(self, docs, *args, **kwargs):
            return docs

        @requests(on='/return_none')
        def return_none(self, docs, *args, **kwargs):
            return None

        @requests(on='/return_copy')
        def return_copy(self, docs, *args, **kwargs):
            import copy

            return copy.copy(docs)

        @requests(on='/return_deepcopy')
        def return_deep_copy(self, docs, *args, **kwargs):
            import copy

            return copy.deepcopy(docs)

    mock = mocker.Mock()
    with Flow().add(uses=MyExecutor) as flow:
        flow.post(inputs=test_docs, on='/return_docs', on_done=mock)
        validate_callback(mock, assert_response)
        flow.post(inputs=test_docs, on='/return_none', on_done=mock)
        validate_callback(mock, assert_response)
        flow.post(inputs=test_docs, on='/return_copy', on_done=mock)
        validate_callback(mock, assert_response)
        flow.post(inputs=test_docs, on='/return_deepcopy', on_done=mock)
        validate_callback(mock, assert_response)
