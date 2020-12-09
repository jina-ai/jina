from pathlib import Path

import pytest

from jina import Document
from jina.flow import Flow

cur_dir = Path(__file__).parent
NUM_DOCS = 10


@pytest.fixture
def input_generator():
    for i in range(0, int(NUM_DOCS)):
        with Document() as d:
            if i < int(NUM_DOCS) / 2:
                d.tags['split'] = 'split1'
            else:
                d.tags['split'] = 'split2'
        yield d


def test_merge_request(mocker, input_generator):
    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS

    response_mock = mocker.Mock(wraps=validate_response)

    with Flow.load_config(str(cur_dir / 'flow.yml')) as f:
        f.index(input_fn=input_generator,
                output_fn=response_mock,
                batch_size=NUM_DOCS)
    response_mock.assert_called()
