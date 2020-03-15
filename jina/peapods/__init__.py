from typing import Dict, Union

from .. import __default_host__

if False:
    import argparse


def Pea(args: 'argparse.Namespace', allow_remote: bool = True):
    """Initialize a :class:`BasePea`, :class:`RemotePea` or :class:`ContainerPea`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemotePea`
    """
    if allow_remote and args.host != __default_host__:
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
        from .pod import ParsedPod
        return ParsedPod(args)
    if allow_remote and args.host != __default_host__:
        from .remote import RemotePod
        return RemotePod(args)
    else:
        from .pod import BasePod
        return BasePod(args)
