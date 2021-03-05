import os

import numpy as np
import pytest

from jina import Document
from jina.clients import Client
from jina.clients.sugary_io import (
    _input_files,
    _input_lines,
    _input_ndarray,
    _input_csv,
)
from jina.enums import DataInputType
from jina.excepts import BadClientInput

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def filepath(tmpdir):
    input_filepath = os.path.join(tmpdir, 'input_file.csv')
    with open(input_filepath, 'w') as input_file:
        input_file.writelines(["1\n", "2\n", "3\n"])
    return input_filepath


def test_input_lines_with_filepath(filepath):
    result = list(_input_lines(filepath=filepath, size=2))
    assert len(result) == 2
    assert isinstance(result[0], Document)


def test_input_csv_from_file():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        result = list(_input_csv(fp))
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'


def test_input_csv_from_lines():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        result = list(_input_lines(fp, line_format='csv'))
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'


def test_input_csv_from_lines_field_resolver():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        result = list(
            _input_lines(
                fp, line_format='csv', field_resolver={'url': 'uri', 'question': 'text'}
            )
        )
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'
    assert result[0].uri
    assert result[0].text


def test_input_csv_from_strings():
    with open(os.path.join(cur_dir, 'docs.csv')) as fp:
        lines = fp.readlines()
    result = list(_input_csv(lines))
    assert len(result) == 2
    assert isinstance(result[0], Document)
    assert result[0].tags['source'] == 'testsrc'


def test_input_lines_with_empty_filepath_and_lines():
    with pytest.raises(ValueError):
        lines = _input_lines(lines=None, filepath=None)
        for _ in lines:
            pass


def test_input_lines_with_jsonlines_docs():
    result = list(_input_lines(filepath='tests/unit/clients/python/docs.jsonlines'))
    assert len(result) == 2
    assert result[0].text == "a"
    assert result[1].text == "b"


def test_input_lines_with_jsonlines_docs_groundtruth():
    result = list(
        _input_lines(filepath='tests/unit/clients/python/docs_groundtruth.jsonlines')
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
def test_input_files(patterns, recursive, size, sampling_rate, read_mode):
    Client.check_input(
        _input_files(
            patterns=patterns,
            recursive=recursive,
            size=size,
            sampling_rate=sampling_rate,
            read_mode=read_mode,
        ),
        data_type=DataInputType.CONTENT,
    )


def test_input_files_with_invalid_read_mode():
    with pytest.raises(BadClientInput):
        Client.check_input(_input_files(patterns='*.*', read_mode='invalid'))


@pytest.mark.parametrize(
    'array', [np.random.random([100, 4, 2]), ['asda', 'dsadas asdasd']]
)
def test_input_numpy(array):
    Client.check_input(_input_ndarray(array))
