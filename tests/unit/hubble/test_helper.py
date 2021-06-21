import os
import json
import pytest

import tempfile
from pathlib import Path
from jina.hubble import helper

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_md5file():
    md5sum = helper.md5file(Path(cur_dir) / 'dummy_executor.zip')
    assert md5sum == '4cda7063c8f81d53c65d621ec1b29124'


def test_archive_package():
    pkg_path = Path(cur_dir) / 'dummy_executor'

    stream_data = helper.archive_package(pkg_path)
    temp_zip_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
    temp_zip_file.write(stream_data.getvalue())
    temp_zip_file.close()

    Path(temp_zip_file.name).unlink()


def test_unpack_package():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        helper.unpack_package(Path(cur_dir) / 'dummy_executor.zip', tmpdirname)
