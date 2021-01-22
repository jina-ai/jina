import copy
from argparse import Namespace
from typing import List

from ... import __default_host__
from ...enums import SchedulerType, SocketType, PeaRoleType
from ...helper import random_port, random_identity, get_public_ip, get_internal_ip, is_valid_local_config_source


def _set_peas_args(args: Namespace, head_args: Namespace = None, tail_args: Namespace = None) -> List[Namespace]:
    result = []

    for idx in range(args.parallel):
        _args = copy.deepcopy(args)
        if head_args:
            _args.port_in = head_args.port_out
        if tail_args:
            _args.port_out = tail_args.port_in
        _args.port_ctrl = random_port()
        _args.socket_out = SocketType.PUSH_CONNECT
        if args.polling.is_push:
            if args.scheduling == SchedulerType.ROUND_ROBIN:
                _args.socket_in = SocketType.PULL_CONNECT
            elif args.scheduling == SchedulerType.LOAD_BALANCE:
                _args.socket_in = SocketType.DEALER_CONNECT
            else:
                raise NotImplementedError
        else:
            _args.socket_in = SocketType.SUB_CONNECT
        if head_args:
            _args.host_in = _fill_in_host(bind_args=head_args, connect_args=_args)
        if tail_args:
            _args.host_out = _fill_in_host(bind_args=tail_args, connect_args=_args)

        if args.parallel > 1:
            _args.pea_id = idx + 1  #: if it is parallel, then pea_id is 1-indexed
            _args.pea_role = PeaRoleType.PARALLEL
            if _args.name:
                _args.name += f'/{_args.pea_id}'
            else:
                _args.name = f'{_args.pea_id}'
        else:
            _args.pea_id = 0
            _args.pea_role = PeaRoleType.SINGLETON

        result.append(_args)
    return result


def _set_after_to_pass(args):
    # TODO: I don't remember what is this for? once figure out, this function should be removed
    # remark 1: i think it's related to route driver.
    if hasattr(args, 'polling') and args.polling.is_push:
        # ONLY reset when it is push
        args.uses_after = '_pass'


def _copy_to_head_args(args: Namespace, is_push: bool, as_router: bool = True) -> Namespace:
    """Set the outgoing args of the head router
    """

    _head_args = copy.deepcopy(args)
    _head_args.port_ctrl = random_port()
    _head_args.port_out = random_port()
    _head_args.uses = None
    if is_push:
        if args.scheduling == SchedulerType.ROUND_ROBIN:
            _head_args.socket_out = SocketType.PUSH_BIND
            if as_router:
                _head_args.uses = args.uses_before or '_pass'
        elif args.scheduling == SchedulerType.LOAD_BALANCE:
            _head_args.socket_out = SocketType.ROUTER_BIND
            if as_router:
                _head_args.uses = args.uses_before or '_pass'
    else:
        _head_args.socket_out = SocketType.PUB_BIND
        if as_router:
            _head_args.uses = args.uses_before or '_pass'

    if as_router:
        _head_args.pea_role = PeaRoleType.HEAD
        if args.name:
            _head_args.name = f'{args.name}/head'
        else:
            _head_args.name = f'head'

    # in any case, if header is present, it represent this Pod to consume `num_part`
    # the following peas inside the pod will have num_part=1
    args.num_part = 1

    return _head_args


def _copy_to_tail_args(args: Namespace, as_router: bool = True) -> Namespace:
    """Set the incoming args of the tail router
    """
    _tail_args = copy.deepcopy(args)
    _tail_args.port_in = random_port()
    _tail_args.port_ctrl = random_port()
    _tail_args.socket_in = SocketType.PULL_BIND
    _tail_args.uses = None

    if as_router:
        _tail_args.uses = args.uses_after or '_pass'
        if args.name:
            _tail_args.name = f'{args.name}/tail'
        else:
            _tail_args.name = f'tail'
        _tail_args.pea_role = PeaRoleType.TAIL
        _tail_args.num_part = 1 if args.polling.is_push else args.parallel

    return _tail_args


def _fill_in_host(bind_args: Namespace, connect_args: Namespace) -> str:
    """Compute the host address for ``connect_args`` """
    from sys import platform

    # by default __default_host__ is 0.0.0.0

    # is BIND at local
    bind_local = (bind_args.host == __default_host__)

    # is CONNECT at local
    conn_local = (connect_args.host == __default_host__)

    # is CONNECT inside docker?
    conn_docker = (getattr(connect_args, 'uses', None) is not None and
                   connect_args.uses.startswith('docker://'))

    # is BIND & CONNECT all on the same remote?
    bind_conn_same_remote = not bind_local and not conn_local and \
                            (bind_args.host == connect_args.host)

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
        return get_public_ip() if bind_args.expose_public else get_internal_ip()
    else:
        # in this case we (at local) need to know about remote the BIND address
        return bind_args.host
