import pytest

from jina import Document, Flow
from jina.helloworld.chatbot.app import hello_world
from jina.helloworld.chatbot.executors import MyTransformer, MyIndexer
from jina.parsers.helloworld import set_hw_chatbot_parser
from tests import validate_callback


@pytest.fixture
def helloworld_args(tmpdir):
    return set_hw_chatbot_parser().parse_args(
        ['--workdir', str(tmpdir), '--unblock-query-flow']
    )


@pytest.fixture
def expected_result():
    return '''no evidence from the outbreak that eating garlic, sipping water every 15 minutes or taking vitamin C will protect people from the new coronavirus.'''


def search(query_document, on_done_callback, on_fail_callback, top_k):
    with Flow().add(uses=MyTransformer).add(uses=MyIndexer) as f:
        f.search(
            inputs=query_document,
            on_done=on_done_callback,
            on_fail=on_fail_callback,
            parameters={'top_k': top_k},
        )


def test_multimodal(helloworld_args, expected_result, mocker):
    """Regression test for multimodal example."""

    def validate_response(resp):
        assert len(resp.data.docs) == 1
        for doc in resp.data.docs:
            assert len(doc.matches) == 10

    hello_world(helloworld_args)

    mock_on_done = mocker.Mock()
    mock_on_fail = mocker.Mock()

    search(Document(text='Is my dog safe from virus'), mock_on_done, mock_on_fail, 1)

    mock_on_fail.assert_not_called()
    validate_callback(mock_on_done, validate_response)
