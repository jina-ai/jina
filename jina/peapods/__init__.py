__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from .. import __default_host__
from ..enums import RemoteAccessType
from ..helper import is_valid_local_config_source
from ..logging import default_logger
from .peas import BasePea

if False:
    import argparse


def Runtime(args: Optional['argparse.Namespace'] = None,
            allow_remote: bool = True,
            pea_cls: BasePea = BasePea, **kwargs):
    """Initialize a :class:`LocalRuntime`, :class:`ContainerRuntime` or :class:`RemoteRuntime`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemoteRuntime`
    :param pea_cls: declares the type of `Pea` to be instantiated by `LocalRuntime`
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
        from .runtimes.remote.jinad import JinadRemoteRuntime
        return JinadRemoteRuntime(args, kind='pea')
    elif args.uses and not is_valid_local_config_source(args.uses):
        from .runtimes.container import ContainerRuntime
        return ContainerRuntime(args)
    else:
        from .runtimes.local import LocalRuntime
        return LocalRuntime(args, pea_cls=pea_cls)


def Pod(args: Optional['argparse.Namespace'] = None,
        allow_remote: bool = True, **kwargs):
    """Initialize a :class:`BasePod`, :class:`JinadRemoteRuntime`, :class:`MutablePod` or :class:`SSHRuntime`

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
                from .runtimes.remote.jinad import JinadRemoteRuntime
                return JinadRemoteRuntime(args, kind='pod')

    if not allow_remote and args.host != __default_host__:
        args.host = __default_host__
        default_logger.warning(f'host is reset to {__default_host__} as allow_remote=False')

    if args.host != __default_host__:
        if args.remote_access == RemoteAccessType.JINAD:
            from .runtimes.remote.jinad import JinadRemoteRuntime
            return JinadRemoteRuntime(args, kind='pod')
        elif args.remote_access == RemoteAccessType.SSH:
            from .runtimes.remote.ssh import SSHRuntime
            return SSHRuntime(args, kind='pod')
        else:
            raise ValueError(f'{args.remote_access} is not supported')
    else:
        from .pods import BasePod
        return BasePod(args)
