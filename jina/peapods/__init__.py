__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Union

from .. import __default_host__
from ..enums import PeaRoleType, RemoteAccessType
from ..helper import is_valid_local_config_source
from ..logging import default_logger

if False:
    import argparse


def Pea(args: 'argparse.Namespace' = None, allow_remote: bool = True, **kwargs):
    """Initialize a :class:`BasePea`, :class:`RemoteSSHPea` or :class:`ContainerPea`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemoteSSHPea`
    :param kwargs: all supported arguments from CLI

    """
    if args is None:
        from ..parser import set_pea_parser
        from ..helper import get_parsed_args
        _, args, _ = get_parsed_args(kwargs, set_pea_parser(), 'Pea')
    if not allow_remote:
        # set the host back to local, as for the remote, it is running "locally"
        if args.host != __default_host__:
            args.host = __default_host__
            default_logger.warning(f'setting host to {__default_host__} as allow_remote set to False')

    if args.host != __default_host__:
        from .remote import RemotePea
        return RemotePea(args)
    elif args.uses and not is_valid_local_config_source(args.uses):
        from .container import ContainerPea
        return ContainerPea(args)
    elif args.role == PeaRoleType.HEAD:
        from .head_pea import HeadPea
        return HeadPea(args)
    elif args.role == PeaRoleType.TAIL:
        from .tail_pea import TailPea
        return TailPea(args)
    else:
        from .pea import BasePea
        return BasePea(args)


def Pod(args: Union['argparse.Namespace', Dict] = None, allow_remote: bool = True, **kwargs):
    """Initialize a :class:`BasePod`, :class:`RemoteSSHPod`, :class:`MutablePod` or :class:`RemoteSSHMutablePod`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemoteSSHPod`
    :param kwargs: all supported arguments from CLI
    """

    if args is None:
        from ..parser import set_pod_parser
        from ..helper import get_parsed_args
        _, args, _ = get_parsed_args(kwargs, set_pod_parser(), 'Pod')
    if isinstance(args, dict):
        hosts = set()
        for k in args.values():
            if k:
                if not isinstance(k, list):
                    k = [k]
                for kk in k:
                    if not allow_remote and kk.host != __default_host__:
                        kk.host = __default_host__
                        default_logger.warning(f'host is reset to {__default_host__} as allow_remote=False')
                    hosts.add(kk.host)

        if len(hosts) == 1:
            if __default_host__ in hosts:
                from .pod import MutablePod
                return MutablePod(args)
            else:
                # TODO: this part needs to be refactored
                from .remote import RemoteMutablePod
                return RemoteMutablePod(args)

    if not allow_remote and args.host != __default_host__:
        args.host = __default_host__
        default_logger.warning(f'host is reset to {__default_host__} as allow_remote=False')

    if args.host != __default_host__:
        if args.remote_access == RemoteAccessType.JINAD:
            from .remote import RemotePod
            return RemotePod(args)
        elif args.remote_access == RemoteAccessType.SSH:
            from .ssh import RemoteSSHPod
            return RemoteSSHPod(args)
        else:
            raise ValueError(f'{args.remote_access} is not supported')

    else:
        from .pod import BasePod
        return BasePod(args)
