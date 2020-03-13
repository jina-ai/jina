from .. import __default_host__

if False:
    import argparse


def get_pea(args: 'argparse.Namespace', allow_remote: bool = True):
    """Initialize a :class:`Pea`, :class:`RemotePea` or :class:`ContainerPea`

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
        from .pea import Pea
        return Pea(args)


def get_pod(args: 'argparse.Namespace', allow_remote: bool = True):
    """Initialize a :class:`Pod`, :class:`RemotePod`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemotePod`
    """
    if allow_remote and args.host != __default_host__:
        from .remote import RemotePod
        return RemotePod(args)
    else:
        from .pod import Pod
        return Pod(args)
