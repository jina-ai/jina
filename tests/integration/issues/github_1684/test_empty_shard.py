import os

import pytest
import numpy as np

from jina.flow import Flow
from jina import Document

from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def workdir(tmpdir):
    os.environ['JINA_TEST_1684_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['JINA_TEST_1684_WORKSPACE']


def test_empty_shard(mocker, workdir):
    doc = Document()
    doc.text = 'text'
    doc.embedding = np.array([1, 1, 1])

    def validate_response(resp):
        assert len(resp.docs) == 1
        assert len(resp.docs[0].matches) == 0

    mock = mocker.Mock()
    error_mock = mocker.Mock()

    with Flow.load_config(os.path.join(cur_dir, 'flow.yml')) as f:
        f.search([doc], on_done=mock, on_error=error_mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)

    error_mock.assert_not_called()
