import os

import pytest

import jina
from jina.helloworld.fashion.app import hello_world
from jina.helloworld.fashion.my_executors import *
from jina.parsers.helloworld import set_hw_parser


def check_hello_world_results(html_path: str):
    from bs4 import BeautifulSoup
    import re

    with open(html_path, 'r') as fp:
        page = fp.read()
    soup = BeautifulSoup(page)
    table = soup.find('table')
    rows = table.find_all('tr')
    assert len(rows) > 1
    for row in rows[1:]:
        cols = row.find_all('img')
        assert len(cols) > 1  # query + results

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


root_dir = os.path.abspath(os.path.dirname(jina.__file__))
os.environ['PATH'] += os.pathsep + os.path.join(root_dir, 'helloworld/fashion/')


def test_fashion(helloworld_args, query_document, tmpdir):
    """Regression test for fashion example."""

    hello_world(helloworld_args)
    check_hello_world_results(os.path.join(str(tmpdir), 'demo.html'))
