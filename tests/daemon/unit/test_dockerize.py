import platform
from daemon.dockerize import Dockerizer

import pytest


@pytest.mark.parametrize(
    'value, expected',
    (['Linux', '//var/run/docker.sock'], ['Darwin', '/var/run/docker.sock']),
)
def test_sock(value, expected, monkeypatch):
    monkeypatch.setattr(platform, 'system', lambda: value)
    assert Dockerizer.dockersock == expected
