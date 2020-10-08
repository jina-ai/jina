import os

import pytest
import numpy as np

from jina.clients.python import PyClient
from jina.clients.python.io import input_files, input_lines, input_numpy


def test_read_file(tmpdir):
    input_filepath = os.path.join(tmpdir, 'input_file.csv')
    with open(input_filepath, 'w') as input_file:
        input_file.writelines(["1\n", "2\n", "3\n"])
    result = list(input_lines(filepath=input_filepath, size=2))
    assert len(result) == 2
    assert result[0] == "1\n"
    assert result[1] == "2\n"

def test_input_lines_with_empty_filepath_and_lines():
    with pytest.raises(Exception):
        lines = input_lines(lines=None, filepath=None)
        for _ in lines:
            pass

@pytest.mark.parametrize(
    'patterns, recursive, size, sampling_rate, read_mode',
    [
        ('*.*', True, None, None, None),
        ('*.*', False, None, None, None),
        ('*.*', True, 2, None, None),
        ('*.*', True, 2, None, 'rb'),
        ('*.*', True, None, 0.5, None),
    ]
)
def test_input_files(patterns, recursive, size, sampling_rate, read_mode):
    PyClient.check_input(
        input_files(
            patterns=patterns,
            recursive=recursive,
            size=size,
            sampling_rate=sampling_rate,
            read_mode=read_mode
        )
    )

def test_input_files_with_invalid_read_mode():
    with pytest.raises(RuntimeError):
        PyClient.check_input(input_files(patterns='*.*', read_mode='invalid'))

@pytest.mark.parametrize('array', [np.random.random([100, 4, 2]), ['asda', 'dsadas asdasd']])
def test_input_numpy(array):
    PyClient.check_input(input_numpy(array))
