import pytest
import requests
from xprocess import ProcessStarter

from jina.parsers.helloworld import set_hw_chatbot_parser


@pytest.fixture
def chatbot_args(tmpdir):
    return set_hw_chatbot_parser().parse_args(
        ['--workdir', str(tmpdir), '--port-expose', '8080']
    )


@pytest.fixture
def payload():
    return {'top_k': 1, 'data': ['text:Is my dog safe from virus']}


@pytest.fixture
def post_uri():
    return 'http://localhost:8080/search'


@pytest.fixture
def expected_result():
    return '''It's not completely up to you.'''


@pytest.fixture(autouse=True)
def start_server(xprocess, chatbot_args):
    class Starter(ProcessStarter):
        pattern = "You should see a demo page opened in your browser"
        args = ["jina", "hello", "chatbot"]
        max_read_lines = 10000

    xprocess.ensure("server", Starter)
    yield
    xprocess.getinfo("server").terminate()


def test_chatbot(payload, post_uri, expected_result):
    """Regression test for chatbot example."""
    resp = requests.post(post_uri, json=payload)
    assert resp.status_code == 200
    print('-------------------------1111111----')
    print(resp.text)
    assert expected_result in resp.text
