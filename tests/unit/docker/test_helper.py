from pathlib import PosixPath

from jina.docker.helper import credentials_file


def test_credentials_file():
    assert isinstance(credentials_file(), PosixPath)
