from argparse import Namespace
import ipaddress

from .. import __default_host__, __docker_host__
from ..helper import get_public_ip, get_internal_ip


def is_remote_local_connection(first, second):
    if first == 'localhost':
        first = '127.0.0.1'
    if second == 'localhost':
        second = '127.0.0.1'
    first_ip = ipaddress.ip_address(first)
    second_ip = ipaddress.ip_address(second)
    return first_ip.is_global and (second_ip.is_private or second_ip.is_loopback)


def get_connect_host(
    bind_host: str, bind_expose_public: bool, connect_args: Namespace
) -> str:
    """
    Compute the host address for ``connect_args``

    :param bind_host: the ip for binding
    :param bind_expose_public: True, if bind socket should be exposed publicly
    :param connect_args: configuration for the host ip connection
    :return: host ip
    """
    from sys import platform

    # by default __default_host__ is 0.0.0.0

    # is BIND at local
    bind_local = bind_host == __default_host__

    # is CONNECT at local
    conn_local = connect_args.host == __default_host__

    # is CONNECT inside docker?
    # check if `uses` has 'docker://' or,
    # it is a remote pea managed by jinad. (all remote peas are inside docker)
    conn_docker = (
        getattr(connect_args, 'uses', None) is not None
        and (
            connect_args.uses.startswith('docker://')
            or connect_args.uses.startswith('jinahub+docker://')
        )
    ) or not conn_local

    # is BIND & CONNECT all on the same remote?
    bind_conn_same_remote = (
        not bind_local and not conn_local and (bind_host == connect_args.host)
    )

    # for remote peas managed by jinad, always set to __docker_host__
    if not conn_local:
        local_host = __docker_host__
    elif platform in ('linux', 'linux2'):
        local_host = __default_host__
    else:
        local_host = __docker_host__

    # pod1 in local, pod2 in local (conn_docker if pod2 in docker)
    if bind_local and conn_local:
        return local_host if conn_docker else __default_host__

    # pod1 and pod2 are remote but they are in the same host (pod2 is local w.r.t pod1)
    if bind_conn_same_remote:
        return local_host if conn_docker else __default_host__

    if bind_local and not conn_local:
        # in this case we are telling CONN (at remote) our local ip address
        if connect_args.host.startswith('localhost'):
            # this is for the "psuedo" remote tests to pass
            return __docker_host__
        return get_public_ip() if bind_expose_public else get_internal_ip()
    else:
        # in this case we (at local) need to know about remote the BIND address
        return bind_host
