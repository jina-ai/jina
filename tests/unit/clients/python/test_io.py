import os

from jina.clients.python.io import input_lines


def test_read_file(tmpdir):
    input_filepath = os.path.join(tmpdir, 'input_file.csv')
    with open(input_filepath, 'w') as input_file:
        input_file.writelines(["1\n", "2\n", "3\n"])
    result = list(input_lines(filepath=input_filepath, size=2))
    assert len(result) == 2
    assert result[0] == "1\n"
    assert result[1] == "2\n"
