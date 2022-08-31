import pytest

from jina import Flow

num_calls = 0


@pytest.fixture(scope='function', autouse=True)
def patched_path_import(mocker):
    from jina.importer import _path_import

    def _wrapped_path_import(absolute_path: str):
        global num_calls
        num_calls += 1
        assert num_calls < 2
        return _path_import(absolute_path)

    mocker.patch(
        'jina.importer._path_import', new_callable=lambda: _wrapped_path_import
    )


def test_single_import(patched_path_import):
    flow = Flow().add(
        uses='ExecutorImportedOnce',
        py_modules=['executors/executor_fails_import_twice.py'],
    )
    with flow:
        pass


def test_single_import_metas(patched_path_import):
    flow = Flow().add(
        uses='ExecutorImportedOnce',
        py_modules=['executors/executor_fails_import_twice.py'],
    )
    with flow:
        pass
