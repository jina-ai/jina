import os
import pytest

from jina.flow import Flow
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina import Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def tmp_workspace(tmpdir):
    os.environ['TMP_2230_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['TMP_2230_WORKSPACE']


@pytest.fixture()
def docs():
    return [Document() for _ in range(100)]


class MockIndexer(BinaryPbIndexer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delete_on_dump = True

    def add(self, *args, **kwargs):
        import time

        time.sleep(1)
        return super().add(*args, **kwargs)


def test_file_handler_not_closed(mocker, docs, tmp_workspace):
    mock = mocker.Mock()
    error_mock = mocker.Mock()

    with Flow().add(
        uses=os.path.join(cur_dir, 'mock_indexer.yml'), dump_interval=1
    ) as f:
        f.index(inputs=docs, request_size=50, on_done=mock, on_error=error_mock)

    mock.assert_called()
    error_mock.assert_not_called()
