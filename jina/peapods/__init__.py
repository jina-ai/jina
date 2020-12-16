__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from .. import __default_host__
from ..enums import RemoteAccessType
from ..helper import is_valid_local_config_source
from ..logging import default_logger

if False:
    import argparse


def RuntimePea(args: Optional['argparse.Namespace'] = None,
               allow_remote: bool = True, **kwargs):
    """Initialize a :class:`LocalRunTime`, :class:`ContainerRunTime` or :class:`RemoteJinaDRunTime`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemoteRuntime`
    :param kwargs: all supported arguments from CLI

    """
    if args is None:
        from ..parser import set_pea_parser
        from ..helper import get_parsed_args
        _, args, _ = get_parsed_args(kwargs, set_pea_parser())
    if not allow_remote:
        # set the host back to local, as for the remote, it is running "locally"
        if args.host != __default_host__:
            args.host = __default_host__
            default_logger.warning(f'setting host to {__default_host__} as allow_remote set to False')

    if args.host != __default_host__:
        from .runtimes.remote.jinad import RemoteJinaDRunTime
        return RemoteJinaDRunTime(args, kind='pea')
    elif args.uses and not is_valid_local_config_source(args.uses):
        from .runtimes.container import ContainerRunTime
        return ContainerRunTime(args)
    else:
        from .runtimes.local import LocalRunTime
        return LocalRunTime(args)


def Pod(args: Optional['argparse.Namespace'] = None,
        allow_remote: bool = True, **kwargs):
    """Initialize a :class:`BasePod`, :class:`RemoteJinaDRunTime`, :class:`MutablePod` or :class:`RemoteSSHRunTime`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemoteSSHPod`
    :param kwargs: all supported arguments from CLI
    """
    if args is None:
        from ..parser import set_pod_parser
        from ..helper import get_parsed_args
        _, args, _ = get_parsed_args(kwargs, set_pod_parser())
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
                from .pods.mutable import MutablePod
                return MutablePod(args)
            else:
                from .runtimes.remote.jinad import RemoteJinaDRunTime
                return RemoteJinaDRunTime(args, kind='pod')

    if not allow_remote and args.host != __default_host__:
        args.host = __default_host__
        default_logger.warning(f'host is reset to {__default_host__} as allow_remote=False')

    if args.host != __default_host__:
        if args.remote_access == RemoteAccessType.JINAD:
            from .runtimes.remote.jinad import RemoteJinaDRunTime
            return RemoteJinaDRunTime(args, kind='pod')
        elif args.remote_access == RemoteAccessType.SSH:
            from .runtimes.remote.ssh import RemoteSSHRunTime
            return RemoteSSHRunTime(args, kind='pod')
        else:
            raise ValueError(f'{args.remote_access} is not supported')
    else:
        from .pods import BasePod
        return BasePod(args)
