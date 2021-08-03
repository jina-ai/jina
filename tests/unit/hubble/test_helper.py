import os
import json
import urllib

import pytest

import tempfile
from pathlib import Path
from jina.hubble import helper
from jina.hubble.helper import disk_cache_offline


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


def test_disk_cache(tmpfile):
    raise_exception = True

    @disk_cache_offline(cache_file=str(tmpfile))
    def _myfunc() -> bool:
        if raise_exception:
            raise urllib.error.URLError('Failing')
        else:
            return True

    # test fails
    with pytest.raises(urllib.error.URLError) as info:
        _myfunc()
    assert 'Failing' in str(info.value)

    raise_exception = False
    # saves result in cache
    assert _myfunc()

    raise_exception = True
    # defaults to cache
    assert _myfunc()
