import numpy as np
import os

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


def test_io_files():
    PyClient.check_input(input_files('*.*'))
    PyClient.check_input(input_files('*.*', recursive=True))
    PyClient.check_input(input_files('*.*', size=2))
    PyClient.check_input(input_files('*.*', size=2, read_mode='rb'))
    PyClient.check_input(input_files('*.*', sampling_rate=0.5))


def test_io_np():
    PyClient.check_input(input_numpy(np.random.random([100, 4, 2])))
    PyClient.check_input(['asda', 'dsadas asdasd'])
