import os

import numpy as np
import pytest
from pkg_resources import resource_filename

from jina import Document
from jina.flow import Flow
from jina.helloworld.fashion.app import hello_world
from jina.parsers.helloworld import set_hw_parser
from tests import validate_callback


def check_hello_world_results(html_path: str):
    from bs4 import BeautifulSoup
    import re

    with open(html_path, 'r') as fp:
        page = fp.read()
    soup = BeautifulSoup(page)
    table = soup.find('table')
    rows = table.find_all('tr')
    assert len(rows) == 129
    for row in rows[1:]:
        cols = row.find_all('img')
        assert len(cols) == 51  # query + results

    evaluation = soup.find_all('h3')[0].text
    assert 'Precision@50' in evaluation
    assert 'Recall@50' in evaluation
    evaluation_results = re.findall(r'\d+\.\d+', evaluation)
    assert len(evaluation_results) == 2
    # not exact to avoid instability, but enough accurate to current results to raise some alarms
    assert float(evaluation_results[0]) > 50.0
    assert float(evaluation_results[1]) >= 0.5


@pytest.fixture
def helloworld_args(tmpdir):
    return set_hw_parser().parse_args(['--workdir', str(tmpdir)])


@pytest.fixture
def query_document():
    return Document(content=np.random.rand(28, 28))


def test_fashion(helloworld_args, query_document, mocker, tmpdir):
    """Regression test for fashion example."""

    def validate_response(resp):
        assert len(resp.search.docs) == 1
        for doc in resp.search.docs:
            assert len(doc.matches) == 10

    hello_world(helloworld_args)
    check_hello_world_results(os.path.join(str(tmpdir), 'demo.html'))
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
