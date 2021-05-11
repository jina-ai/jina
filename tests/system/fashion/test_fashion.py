import os

import numpy as np
import pytest
from pkg_resources import resource_filename

from jina import Document
from jina.flow import Flow
from jina.helloworld.fashion.app import hello_world
from jina.parsers.helloworld import set_hw_parser
from tests import validate_callback


@pytest.fixture
def helloworld_args(tmpdir):
    return set_hw_parser().parse_args(['--workdir', str(tmpdir)])


@pytest.fixture
def query_document():
    return Document(content=np.random.rand(28, 28))


def test_fashion(helloworld_args, query_document, mocker):
    """Regression test for fashion example."""

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        for doc in resp.search.docs:
            assert len(doc.matches) == 10

    hello_world(helloworld_args)
    flow_query_path = os.path.join(resource_filename('jina', 'resources'), 'fashion')

    mock_on_done = mocker.Mock()
    mock_on_fail = mocker.Mock()

    with Flow.load_config(
        os.path.join(flow_query_path, 'helloworld.flow.query.yml')
    ) as f:
        f.search(
            inputs=[query_document],
            on_done=mock_on_done,
            on_fail=mock_on_fail,
            top_k=10,
        )

    mock_on_fail.assert_not_called()
    validate_callback(mock_on_done, validate_response)
