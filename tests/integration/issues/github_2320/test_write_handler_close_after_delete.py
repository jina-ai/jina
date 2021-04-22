import pytest

from jina.flow import Flow
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina import Document


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


def test_file_handler_not_closed(mocker, docs):
    mock = mocker.Mock()
    error_mock = mocker.Mock()

    with Flow().add(uses=MockIndexer, dump_interval=1) as f:
        f.index(inputs=docs, request_size=50, on_done=mock, on_error=error_mock)

    mock.assert_called_at_least_once()
    error_mock.assert_not_called()
