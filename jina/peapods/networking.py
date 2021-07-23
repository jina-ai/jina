from argparse import Namespace
import ipaddress

from .. import __default_host__, __docker_host__
from ..helper import get_public_ip, get_internal_ip


def is_remote_local_connection(first: str, second: str):
    """
    Decides, whether ``first`` is remote host and ``second`` is localhost

    :param first: the ip or host name of the first runtime
    :param second: the ip or host name of the second runtime
    :return: True, if first is remote and second is local
    """

    try:
        first_ip = ipaddress.ip_address(first)
        first_global = first_ip.is_global
    except ValueError:
        if first == 'localhost':
            first_global = False
        else:
            first_global = True
    try:
        second_ip = ipaddress.ip_address(second)
        second_local = second_ip.is_private or second_ip.is_loopback
    except ValueError:
        if second == 'localhost':
            second_local = True
        else:
            second_local = False

    return first_global and second_local


def get_connect_host(
    bind_host: str,
    bind_expose_public: bool,
    connect_args: Namespace,
) -> str:
    """
    Compute the host address for ``connect_args``

    :param bind_host: the ip for binding
    :param bind_expose_public: True, if bind socket should be exposed publicly
    :param connect_args: configuration for the host ip connection
    :return: host ip
    """
    runs_in_docker = connect_args.runs_in_docker
    # by default __default_host__ is 0.0.0.0

    # is BIND at local
    bind_local = bind_host == __default_host__

    # is CONNECT at local
    conn_local = connect_args.host == __default_host__

    # is CONNECT inside docker?
    # check if `uses` has 'docker://' or,
    # it is a remote pea managed by jinad. (all remote peas are inside docker)
    conn_docker = (
        (
            getattr(connect_args, 'uses', None) is not None
            and (
                connect_args.uses.startswith('docker://')
                or connect_args.uses.startswith('jinahub+docker://')
            )
        )
        or not conn_local
        or runs_in_docker
    )

    # is BIND & CONNECT all on the same remote?
    bind_conn_same_remote = (
        not bind_local and not conn_local and (bind_host == connect_args.host)
    )

    # pod1 in local, pod2 in local (conn_docker if pod2 in docker)
    if bind_local and conn_local:
        return __docker_host__ if conn_docker else __default_host__

    # pod1 and pod2 are remote but they are in the same host (pod2 is local w.r.t pod1)
    if bind_conn_same_remote:
        return __docker_host__ if conn_docker else __default_host__

    if bind_local and not conn_local:
        # in this case we are telling CONN (at remote) our local ip address
        if connect_args.host.startswith('localhost'):
            # this is for the "psuedo" remote tests to pass
            return __docker_host__
        return get_public_ip() if bind_expose_public else get_internal_ip()
    else:
        # in this case we (at local) need to know about remote the BIND address
        return bind_host
