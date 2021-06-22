from argparse import Namespace

from .. import __default_host__
from ..helper import get_public_ip, get_internal_ip


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
    conn_docker = getattr(
        connect_args, 'uses', None
    ) is not None and connect_args.uses.startswith('docker://')

    # is BIND & CONNECT all on the same remote?
    bind_conn_same_remote = (
        not bind_local and not conn_local and (bind_host == connect_args.host)
    )

    if platform in ('linux', 'linux2'):
        local_host = __default_host__
    else:
        local_host = 'host.docker.internal'

    # pod1 in local, pod2 in local (conn_docker if pod2 in docker)
    if bind_local and conn_local:
        return local_host if conn_docker else __default_host__

    # pod1 and pod2 are remote but they are in the same host (pod2 is local w.r.t pod1)
    if bind_conn_same_remote:
        return local_host if conn_docker else __default_host__

    # From here: Missing consideration of docker
    if bind_local and not conn_local:
        # in this case we are telling CONN (at remote) our local ip address
        return get_public_ip() if bind_expose_public else get_internal_ip()
    else:
        # in this case we (at local) need to know about remote the BIND address
        return bind_host
