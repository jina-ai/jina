from pathlib import PosixPath

import pytest

from jina.docker.helper import credentials_file, handle_dot_in_keys, Waiter


@pytest.mark.parametrize(
    'seconds, expected', [(0, True), (10, False)]
)
def test_waiter(seconds, expected):
    with Waiter(seconds=seconds) as waiter:
        waiter.sleep(1)
        assert waiter.is_time_up == expected


def test_credentials_file():
    assert isinstance(credentials_file(), PosixPath)


@pytest.mark.parametrize(
    'document, expected',
    [
        ({'_doc1': 'content'}, {'_doc1': 'content'}),
        ({'.doc1': 'content'}, {'_doc1': 'content'}),
        ({'doc1': {'.doc1': 'content'}}, {'doc1': {'_doc1': 'content'}}),
        ({'doc1': [{'.doc1': 'content'}]}, {'doc1': [{'_doc1': 'content'}]}),
    ]
)
def test_handle_dot_in_keys(document, expected):
    assert handle_dot_in_keys(document) == expected
