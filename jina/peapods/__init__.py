__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from typing import Optional

from .. import __default_host__
from ..enums import RemoteAccessType
from ..logging import default_logger


def Pod(args: Optional['argparse.Namespace'] = None,
        allow_remote: bool = True, **kwargs):
    """Initialize a :class:`BasePod`, :class:`JinadRemoteRuntime`, :class:`MutablePod` or :class:`SSHRuntime`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemoteSSHPod`
    :param kwargs: all supported arguments from CLI
    """
    if args is None:
        from ..parser import set_pod_parser
        from ..helper import ArgNamespace
        args = ArgNamespace.kwargs2namespace(kwargs, set_pod_parser())
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
                from jina.peapods.runtimes.jinad import JinadRemoteRuntime
                return JinadRemoteRuntime(args, kind='pod')

    if not allow_remote and args.host != __default_host__:
        args.host = __default_host__
        default_logger.warning(f'host is reset to {__default_host__} as allow_remote=False')

    if args.host != __default_host__:
        if args.remote_access == RemoteAccessType.JINAD:
            from jina.peapods.runtimes.jinad import JinadRemoteRuntime
            return JinadRemoteRuntime(args, kind='pod')
        elif args.remote_access == RemoteAccessType.SSH:
            from jina.peapods.runtimes.ssh import SSHRuntime
            return SSHRuntime(args, kind='pod')
        else:
            raise ValueError(f'{args.remote_access} is not supported')
    else:
        from .pods import BasePod
        return BasePod(args)
