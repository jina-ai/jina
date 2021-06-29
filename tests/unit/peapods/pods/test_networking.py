from jina.helper import get_internal_ip
from jina import __default_host__, __docker_host__
from jina.peapods.networking import get_connect_host, is_remote_local_connection
from jina.parsers import set_pea_parser

import pytest

docker_uses = 'docker://abc'


@pytest.mark.parametrize(
    'bind_host, connect_host, connect_uses, expected_connect_host',
    [
        (
            __default_host__,
            __default_host__,
            None,
            __default_host__,
        ),  # local bind & local connect
        (
            __default_host__,
            __default_host__,
            docker_uses,
            __default_host__,
        ),  # local bind & local connect, connect inside docker
        (
            '1.2.3.4',
            __default_host__,
            None,
            '1.2.3.4',
        ),  # remote bind & local connect
        (
            '1.2.3.4',
            __default_host__,
            docker_uses,
            '1.2.3.4',
        ),  # remote bind & local connect, connect inside docker
        (
            __default_host__,
            'localhost:8000',
            None,
            __docker_host__,
        ),  # local bind & "pseudo" remote connect (used in tests), should be dockerhost
        (
            __default_host__,
            'localhost:8000',
            docker_uses,
            __docker_host__,
        ),  # local bind & "pseudo" remote connect (used in tests), should be dockerhost
        (
            __default_host__,
            '1.2.3.4',
            None,
            get_internal_ip(),
        ),  # local bind, remote connect
        (
            __default_host__,
            '1.2.3.4',
            docker_uses,
            get_internal_ip(),
        ),  # local bind, remote connect, connect inside docker
        (
            '1.2.3.4',
            '1.2.3.4',
            None,
            __docker_host__,
        ),  # bind and connect same remote
        (
            '1.2.3.4',
            '1.2.3.4',
            None,
            __docker_host__,
        ),  # bind and connect same remote, connect inside docker
        ('2.3.4.5', '1.2.3.4', None, '2.3.4.5'),  # bind and connect diff remotes
        (
            '2.3.4.5',
            '1.2.3.4',
            docker_uses,
            '2.3.4.5',
        ),  # bind and connect diff remotes, connect inside docker
    ],
)
def test_get_connect_host(connect_host, bind_host, connect_uses, expected_connect_host):
    connect_args = set_pea_parser().parse_args(
        ['--host', connect_host, '--uses', connect_uses]
    )
    connect_host = get_connect_host(
        bind_host=bind_host,
        bind_expose_public=False,
        connect_args=connect_args,
    )
    assert connect_host == expected_connect_host


def test_is_remote_local_connection():
    assert not is_remote_local_connection('0.0.0.0', '0.0.0.0')
    assert not is_remote_local_connection('localhost', 'localhost')
    assert not is_remote_local_connection('localhost', '1.2.3.4')
    assert not is_remote_local_connection('1.2.3.4', '2.3.4.5')
    assert not is_remote_local_connection('127.0.0.1', 'localhost')
    assert not is_remote_local_connection('192.168.0.1', 'localhost')

    assert is_remote_local_connection('1.2.3.4', 'localhost')
    assert is_remote_local_connection('1.2.3.4', '192.168.0.1')
