import multiprocessing as mp
import sys
import time

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
    return '''It's not completely up to you.'''


def test_chatbot(helloworld_args, expected_result, payload, post_uri):
    """Regression test for chatbot example."""
    p = mp.Process(target=hello_world, args=(helloworld_args,))
    p.start()
    time.sleep(30)
    resp = requests.post(post_uri, json=payload)
    assert resp.status_code == 200
    assert expected_result in resp.text
    p.terminate()
    p.join(10)
