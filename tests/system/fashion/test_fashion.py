import os

import pytest
import numpy as np
from pkg_resources import resource_filename

from jina import Document
from jina.flow import Flow
from jina.helloworld.fashion import hello_world
from jina.parsers.helloworld import set_hw_parser
from tests import validate_callback


@pytest.fixture
def helloworld_args(tmpdir):
    return set_hw_parser().parse_args(['--workdir', str(tmpdir)])


@pytest.fixture
def test_query_image():
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAADBklEQVR42q2WwSv7cRjHd3LbZGskLVEjitKiEYUQQghtC5maJsTaFguNHDZJKCVxUy7kJGnEYcpR0drJ9hcstXJwsLfeT83hd/lNfZ5aq2fr+/q8n+/zvJ+PBjnE4eEhTk9Psbu7i+npaczOzmJ+fh5OpxNerxf7+/vINTT/+8Pn5ycmJycxPDyMhoYGVFVVobKyEqWlpSgpKUF1dTWamprUAROJBPr6+lBXV4e2tjaMjo7CYrGgsbERAwMD6Onpkd8+Pj7UAG9vbzE3NydldDgcGBwcRH19PVpaWtDb24vx8XEBPj8/qwGenZ1hYWEBi4uLmJqaQkdHB8rLy2Gz2QS2sbEhKi8vL9UAj46OsLm5iVAoBI/HI8CamhopLxVvb2/L98XFhRrgyckJ1tfX5cEsq8lkgkajEVUrKyuSHxkZUafw6upKxoFQn88Hg8GA1tZWAe7t7WFrawv9/f24ublRA7y+vpaHEra0tCQNEo/HMTY2hnA4LAfp7OzEw8ODGmA0GpXGWF1dlUZhh35/f6O5uVmALCsPEYvF1AD5IKojkEqojNHd3S25QCCA2tpapNNpNcBUKiUjwQ8dxeVySZ4jwvl0u91iBMqcJpPJYGZmRryTNkYAw263/1oelSsDMjgOy8vLqKioEKWMoaEhmT+6DQ+kFLi2tiZAmnYWSE9leemznFWlwIODA/j9fulMlpbR1dUl1sbmeXp6Ugukn1INFbK8DDYKh99qteY8EjkDj4+P0d7ejsLCQuzs7EiOu5HvlHuRK0wpMBgMyuLNz8/H/f295NiZhPEQLy8vaoHcEhxu+mgymZQcly+BRUVF4kZKgbzHsHy8UvDKweAolJWVobi4GI+Pj2qBExMTooSLNxscEyrU6/WIRCJqgXQXo9EIs9n8m2PzUB3fK68hSoG8YvDBfI/ZOD8/F9UFBQW4u7tTD8zLy5PrRTa4/6hQp9PlvAv/1DRarVY2ezZeX1+liQhU3qVcQ/8C39/f5X7D/Nvbm3rz5oDTALLx9fUl+5Gj8Zf4AVzLdWYED1wRAAAAAElFTkSuQmCC'


@pytest.fixture
def query_document(test_query_image):
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
