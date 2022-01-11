import pytest

from jina import __version__
from jina.peapods.pods.config.helper import (
    get_base_executor_version,
    to_compatible_name,
)


@pytest.mark.parametrize('is_master', (True, False))
def test_version(is_master, requests_mock):
    if is_master:
        version = 'v2'
    else:
        # current version is published already
        version = __version__
    requests_mock.get(
        'https://registry.hub.docker.com/v1/repositories/jinaai/jina/tags',
        text='[{"name": "v1"}, {"name": "' + version + '"}]',
    )
    v = get_base_executor_version()
    if is_master:
        assert v == 'master'
    else:
        assert v == __version__


def test_to_compatible_name():
    assert to_compatible_name('executor/hey-ha_HO') == 'executor-hey-ha-ho'
