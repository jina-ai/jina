import urllib

import pytest

from pathlib import Path
from jina.hubble import helper
from jina.hubble.helper import disk_cache_offline
from jina.parsers.hubble import set_hub_pull_parser


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


@pytest.mark.parametrize(
    'uri_path',
    [
        'different-scheme://hello',
        'jinahub://',
    ],
)
def test_parse_wrong_hub_uri(uri_path):
    with pytest.raises(ValueError) as info:
        helper.parse_hub_uri(uri_path)

    assert f'{uri_path} is not a valid Hub URI.' == str(info.value)


def test_md5file(dummy_zip_file):
    md5sum = helper.md5file(dummy_zip_file)
    assert md5sum == '7ffd1501f24fe5a66dc45883550c2005'


def test_archive_package(tmpdir):
    pkg_path = Path(__file__).parent / 'dummy_executor'

    stream_data = helper.archive_package(pkg_path)
    with open(tmpdir / 'dummy_test.zip', 'wb') as temp_zip_file:
        temp_zip_file.write(stream_data.getvalue())


@pytest.mark.parametrize(
    'package_file',
    [
        Path(__file__).parent / 'dummy_executor.zip',
        Path(__file__).parent / 'dummy_executor.tar',
        Path(__file__).parent / 'dummy_executor.tar.gz',
    ],
)
def test_unpack_package(tmpdir, package_file):
    helper.unpack_package(package_file, tmpdir / 'dummy_executor')


def test_unpack_package_unsupported(tmpdir):
    with pytest.raises(ValueError):
        helper.unpack_package(
            Path(__file__).parent / "dummy_executor.unsupported",
            tmpdir / 'dummy_executor',
        )


def test_install_requirements():
    helper.install_requirements(
        Path(__file__).parent / 'dummy_executor' / 'requirements.txt'
    )


def test_is_requirement_installed(tmpfile):
    with open(tmpfile, 'w') as f:
        f.write('jina==0.0.1\npydatest==0.0.1\nfinefinetuner==0.0.1')
    assert not helper.is_requirements_installed(tmpfile)

    with open(tmpfile, 'w') as f:
        f.write('pytest==0.0.1')
    with pytest.warns(None, match='VersionConflict') as record:
        assert helper.is_requirements_installed(tmpfile, show_warning=True)
    assert len(record) == 1

    with pytest.warns(None) as record:
        assert helper.is_requirements_installed(tmpfile, show_warning=False)
    assert len(record) == 0

    with open(tmpfile, 'w') as f:
        f.write('jina-awesome-nonexist')
    assert not helper.is_requirements_installed(tmpfile)
    with pytest.warns(None) as record:
        assert not helper.is_requirements_installed(tmpfile, show_warning=True)
    assert len(record) == 1

    with pytest.warns(None) as record:
        assert not helper.is_requirements_installed(tmpfile, show_warning=False)
    assert len(record) == 0

    with open(tmpfile, 'w') as f:
        f.writelines(['pytest'])
    assert helper.is_requirements_installed(tmpfile)


def test_disk_cache(tmpfile):
    raise_exception = True
    result = 1

    # create an invalid cache file
    with open(str(tmpfile), 'w') as f:
        f.write('Oops: db type could not be determined')

    @disk_cache_offline(cache_file=str(tmpfile))
    def _myfunc(force=False) -> bool:
        if raise_exception:
            raise urllib.error.URLError('Failing')
        else:
            return result

    # test fails
    with pytest.raises(urllib.error.URLError) as info:
        _myfunc()
    assert 'Failing' in str(info.value)

    raise_exception = False
    # returns latest, saves result in cache
    assert _myfunc() == 1

    result = 2
    # does not return latest, defaults to cache since force == False
    assert _myfunc() == 1

    # returns latest since force == True
    assert _myfunc(force=True) == 2

    raise_exception = True
    result = 3
    # does not return latest and exception is not raised, defaults to cache
    assert _myfunc(force=True) == 2
