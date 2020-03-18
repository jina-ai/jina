from typing import Dict, Union

from .. import __default_host__
from ..logging import default_logger

if False:
    import argparse


def Pea(args: 'argparse.Namespace', allow_remote: bool = True):
    """Initialize a :class:`BasePea`, :class:`RemotePea` or :class:`ContainerPea`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemotePea`
    """
    if not allow_remote:
        # set the host back to local, as for the remote, it is running "locally"
        if args.host != __default_host__:
            args.host = __default_host__
            default_logger.warning(f'setting host to {__default_host__} as allow_remote set to False')

    if args.host != __default_host__:
        from .remote import RemotePea
        return RemotePea(args)
    elif args.image:
        from .pea import ContainerPea
        return ContainerPea(args)
    else:
        from .pea import BasePea
        return BasePea(args)


def Pod(args: Union['argparse.Namespace', Dict], allow_remote: bool = True):
    """Initialize a :class:`BasePod`, :class:`RemotePod`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemotePod`
    """
    if isinstance(args, dict):
        if not allow_remote:
            for k in args.values():
                if k:
                    if not isinstance(k, list):
                        k = [k]
                for kk in k:
                    kk.host = __default_host__
        from .pod import ParsedPod
        return ParsedPod(args)

    if not allow_remote:
        if args.host != __default_host__:
            args.host = __default_host__
            default_logger.warning(f'setting host to {__default_host__} as allow_remote set to False')

    if args.host != __default_host__:
        from .remote import RemotePod
        return RemotePod(args)
    else:
        from .pod import BasePod
        return BasePod(args)
