import pytest

from jina import Document
from jina.helloworld.chatbot.app import hello_world, _get_flow
from jina.parsers.helloworld import set_hw_chatbot_parser
from tests import validate_callback


@pytest.fixture
def helloworld_args(tmpdir):
    return set_hw_chatbot_parser().parse_args(
        [
            '--workdir',
            str(tmpdir),
            '--port-expose',
            '8080',
            '--unblock-query-flow',
            '--parallel',
            '1',
        ]
    )


def test_chatbot_helloworld(helloworld_args):
    hello_world(helloworld_args)  # ensure no error is raised.


def test_chatbot(tmpdir, mocker, helloworld_args):
    #  test the index and query flow.
    def validate_response(resp):
        assert len(resp.data.docs) == 1
        for doc in resp.data.docs:
            assert len(doc.matches) == 1
            assert (
                'testing positive means that you have the virus'
                in doc.matches[0].tags['answer']
            )

    mock_on_done = mocker.Mock()
    mock_on_fail = mocker.Mock()

    flow = _get_flow(helloworld_args)
    with flow as f:
        f.index(
            inputs=Document(
                text='Does testing positive mean that I have the virus and that I will develop symptoms?',
                tags={
                    "wrong_answer": "You should take precaution with any containers, Elliott says. \"The plasticgrocery bags I’d throw out right away, wash your hands and then clean yourfood. Chances (of infection) are low,\" she said. \"But better yet, bring yourown bags! It’s better for the environment anyway.\"",
                    "answer": "Yes, testing positive means that you have the virus, but it does not mean that you will develop symptoms. Some people who have the virus don't have any symptoms at all.\n\nAt the same time, testing negative does not necessarily mean that you don't have the virus.",
                },
            ),
        )
        f.search(
            inputs=Document(
                content='Does testing positive mean that I have the virus and that I will develop symptoms?'
            ),
            on_done=mock_on_done,
            on_fail=mock_on_fail,
        )

        mock_on_fail.assert_not_called()
        validate_callback(mock_on_done, validate_response)
