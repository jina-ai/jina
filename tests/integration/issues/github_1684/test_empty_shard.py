import os

import pytest
import numpy as np

from jina.flow import Flow
from jina import Document

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
    mock = mocker.Mock()

    def validate_response(resp):
        mock()
        assert len(resp.docs) == 1
        assert len(resp.docs[0].matches) == 0

    error_mock = mocker.Mock()

    def on_error_call():
        error_mock()

    with Flow.load_config(os.path.join(cur_dir, 'flow.yml')) as f:
        f.search([doc], on_done=validate_response, on_error=on_error_call)

    mock.assert_called_once()
    error_mock.assert_not_called()
