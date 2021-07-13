import os
import json
import pytest

import tempfile
from pathlib import Path
from jina.hubble import helper
from jina.hubble.helper import disk_cache


@pytest.fixture
def dummy_zip_file():
    return Path(__file__).parent / 'dummy_executor.zip'


def test_parse_hub_uri():
    result = helper.parse_hub_uri('jinahub://hello')
    assert result == ('jinahub', 'hello', None, None)

    result = helper.parse_hub_uri('jinahub+docker://hello')
    assert result == ('jinahub+docker', 'hello', None, None)

    result = helper.parse_hub_uri('jinahub+docker://hello/world')
    assert result == ('jinahub+docker', 'hello', 'world', None)

    result = helper.parse_hub_uri('jinahub+docker://hello:magic/world')
    assert result == ('jinahub+docker', 'hello', 'world', 'magic')


def test_md5file(dummy_zip_file):
    md5sum = helper.md5file(dummy_zip_file)
    assert md5sum == '4cda7063c8f81d53c65d621ec1b29124'


def test_archive_package(tmpdir):
    pkg_path = Path(__file__).parent / 'dummy_executor'

    stream_data = helper.archive_package(pkg_path)
    with open(tmpdir / 'dummy_test.zip', 'wb') as temp_zip_file:
        temp_zip_file.write(stream_data.getvalue())


def test_unpack_package(tmpdir, dummy_zip_file):
    helper.unpack_package(dummy_zip_file, tmpdir / 'dummp_executor')


first_time = False


def test_disk_cache(tmpdir):
    global first_time
    tmpfile = f'jina_test_{next(tempfile._get_candidate_names())}.db'

    class _Exception(Exception):
        pass

    @disk_cache((_Exception,), cache_file=str(tmpdir / tmpfile))
    def _myfunc() -> bool:
        global first_time
        if not first_time:
            raise _Exception('Failing')
        else:
            first_time = False
            return True

    # test fails
    with pytest.raises(_Exception) as info:
        _myfunc()
    assert 'Failing' in str(info.value)

    first_time = True
    # saves result in cache in a first try
    assert _myfunc()
    # defaults to cache
    assert _myfunc()
