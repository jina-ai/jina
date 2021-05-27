import time
import threading

import pytest
import requests

from jina.helloworld.chatbot.app import hello_world
from jina.parsers.helloworld import set_hw_chatbot_parser


@pytest.fixture
def helloworld_args(tmpdir):
    return set_hw_chatbot_parser().parse_args(
        ['--workdir', str(tmpdir), '--port-expose', '8080']
    )


@pytest.fixture
def payload():
    return {'data': ['text:Is my dog safe from virus']}


@pytest.fixture
def post_uri():
    return 'http://localhost:8080/search'


@pytest.fixture
def expected_result():
    return '''no evidence from the outbreak that eating garlic, sipping water every 15 minutes or taking vitamin C will protect people from the new coronavirus.'''


def test_multimodal(helloworld_args, expected_result, payload, post_uri):
    """Regression test for helloworld example."""
    thread = threading.Thread(target=hello_world, args=(helloworld_args,))
    thread.daemon = True
    thread.start()
    thread.join(timeout=30)
    resp = requests.post(post_uri, json=payload)
    assert resp.status_code == 200
    assert expected_result in resp.text
