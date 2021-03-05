import pytest
from pkg_resources import resource_stream

from jina.docker.checker import (
    check_name,
    check_version,
    check_image_name,
    check_platform,
    check_license,
    check_image_type,
    remove_control_characters,
    safe_url_name,
    get_exist_path,
    get_summary_path,
    is_error_message,
)
from jina.jaml import JAML


def test_check_name():
    with pytest.raises(ValueError):
        check_name('!JWJPOW"·!"EWQSD')
    check_name('validname')


def test_check_version():
    with pytest.raises(ValueError):
        check_version('0.1.2.3.4.5.8')
    check_version('0.1.5')


def test_check_image_name():
    with pytest.raises(ValueError):
        check_image_name('hbu.jina.pod.')
    check_image_name('hub.jina.pod')


def test_check_platform():
    with resource_stream(
        'jina', '/'.join(('resources', 'hub-builder', 'platforms.yml'))
    ) as fp:
        platforms = JAML.load(fp)
    check_platform(platforms)
    with pytest.raises(ValueError):
        check_platform(platforms + ['invalid'])


def test_check_licenses():
    with resource_stream(
        'jina', '/'.join(('resources', 'hub-builder', 'osi-approved.yml'))
    ) as fp:
        licenses = JAML.load(fp)

    for lic in licenses:
        check_license(lic)

    with pytest.raises(ValueError):
        check_license('invalid')


def test_check_image_type():
    for image_type in ['flow', 'app', 'pod']:
        check_image_type(image_type)

    with pytest.raises(ValueError):
        check_image_type('invalid')


def test_remove_control_parameters():
    removed = remove_control_characters('hey\0here')
    assert removed == 'heyhere'

    good = remove_control_characters('hey here')
    assert good == 'hey here'


def test_safe_url_name():
    safe = safe_url_name('heY_here I am ')
    assert safe == 'hey__here_i_am_'

    good = safe_url_name('heyhere.com')
    assert good == 'heyhere.com'


def test_exist_path(tmpdir):
    import os

    existing = os.path.join(str(tmpdir), 'exists')
    os.mkdir(existing)
    assert get_exist_path(str(tmpdir), 'not_exists') is None


def test_is_error_message():
    for message in ['there is an error', 'it failed', 'there are FAILURES']:
        assert is_error_message(message)

    assert not is_error_message('successful')
