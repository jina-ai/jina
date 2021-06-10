import os

import numpy as np
import pytest

from jina import Document
from jina.clients import Client
from jina.excepts import BadClientInput
from jina.types.document.generators import (
    from_files,
    from_ndarray,
    from_lines,
    from_csv,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def client():
    return Client(host='localhost', port_expose=123456)


@pytest.fixture(scope='function')
def filepath(tmpdir):
    input_filepath = os.path.join(tmpdir, 'input_file.csv')
    with open(input_filepath, 'w') as input_file:
        input_file.writelines(["1\n", "2\n", "3\n"])
    return input_filepath


def test_input_lines_with_filepath(filepath):
    result = list(from_lines(filepath=filepath, size=2))
    assert len(result) == 2
    assert isinstance(result[0], Document)


def test_input_csv_from_file():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        result = list(from_csv(fp))
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'


def test_input_csv_from_lines():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        result = list(from_lines(fp, line_format='csv'))
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'


def test_input_csv_from_lines_field_resolver():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        result = list(
            from_lines(fp, line_format='csv', field_resolver={'question': 'text'})
        )
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'
    assert not result[0].uri
    assert result[0].text


def test_input_csv_from_strings():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        lines = fp.readlines()
    result = list(from_csv(lines))
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'


def test_input_lines_with_empty_filepath_and_lines():
    with pytest.raises(ValueError):
        lines = from_lines(lines=None, filepath=None)
        for _ in lines:
            pass


def test_input_lines_with_jsonlines_docs():
    result = list(from_lines(filepath=os.path.join(cur_dir, 'docs.jsonlines')))
    assert len(result) == 2
    assert result[0].text == "a"
    assert result[1].text == "b"


@pytest.mark.parametrize(
    'size, sampling_rate',
    [
        (None, None),
        (1, None),
        (None, 0.5),
    ],
)
def test_input_lines_with_jsonlines_file(size, sampling_rate):
    result = list(
        from_lines(
            filepath=os.path.join(cur_dir, 'docs.jsonlines'),
            size=size,
            sampling_rate=sampling_rate,
        )
    )
    assert len(result) == size if size is not None else 2
    if sampling_rate is None:
        assert result[0].text == "a"
        if size is None:
            assert result[1].text == "b"


@pytest.mark.parametrize(
    'size, sampling_rate',
    [
        (None, None),
        (1, None),
        (None, 0.5),
    ],
)
def test_input_lines_with_jsonslines(size, sampling_rate):
    with open(os.path.join(cur_dir, 'docs.jsonlines')) as fp:
        lines = fp.readlines()
    result = list(
        from_lines(
            lines=lines, line_format='json', size=size, sampling_rate=sampling_rate
        )
    )
    assert len(result) == size if size is not None else 2
    if sampling_rate is None:
        assert result[0].text == "a"
        if size is None:
            assert result[1].text == "b"


def test_input_lines_with_jsonlines_docs_groundtruth():
    result = list(
        from_lines(filepath='tests/unit/clients/python/docs_groundtruth.jsonlines')
    )
    assert len(result) == 2
    assert result[0][0].text == "a"
    assert result[0][1].text == "b"
    assert result[1][0].text == "c"
    assert result[1][1].text == "d"


@pytest.mark.parametrize(
    'patterns, recursive, size, sampling_rate, read_mode',
    [
        ('*.*', True, None, None, None),
        ('*.*', False, None, None, None),
        ('*.*', True, 2, None, None),
        ('*.*', True, 2, None, 'rb'),
        ('*.*', True, None, 0.5, None),
    ],
)
def test_input_files(patterns, recursive, size, sampling_rate, read_mode, client):
    client.check_input(
        from_files(
            patterns=patterns,
            recursive=recursive,
            size=size,
            sampling_rate=sampling_rate,
            read_mode=read_mode,
        )
    )


def test_input_files_with_invalid_read_mode(client):
    with pytest.raises(BadClientInput):
        client.check_input(from_files(patterns='*.*', read_mode='invalid'))


@pytest.mark.parametrize(
    'array', [np.random.random([100, 4, 2]), ['asda', 'dsadas asdasd']]
)
def test_input_numpy(array, client):
    client.check_input(from_ndarray(array))
