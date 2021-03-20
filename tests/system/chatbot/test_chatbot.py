import os

import pytest
import requests
from pkg_resources import resource_filename

from jina import Document
from jina.flow import Flow
from jina.helloworld.chatbot import hello_world
from jina.parsers.helloworld import set_hw_chatbot_parser
from tests import validate_callback


@pytest.fixture
def chatbot_args(tmpdir):
    return set_hw_chatbot_parser().parse_args(['--workdir', str(tmpdir)])


@pytest.fixture
def payload():
    return {'top_k': 10, 'data': ['text:Is my dog safe from virus']}


@pytest.fixture
def post_uri():
    return 'http://localhost:8080/api/search'


@pytest.fixture
def expected_result():
    return '''There’s no evidence from the outbreak that eating garlic, sipping water every 15 minutes or taking vitamin C will protect people from the new coronavirus.'''


def test_chatbot(chatbot_args, payload, post_uri, expected_result):
    """Regression test for multimodal example."""
    hello_world(chatbot_args)
    resp = requests.post(post_uri, json=payload)
    assert resp.status_code == 200
    assert expected_result in resp.text
