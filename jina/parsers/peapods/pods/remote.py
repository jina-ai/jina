from ...helper import add_arg_group
from ....enums import RemoteAccessType


def mixin_remote_feature_parser(parser):
    """Mixing in arguments required by :class:`BasePod` into the given parser. """
    gp = add_arg_group(parser, title='Distributed')

    gp.add_argument('--remote-manager',
                    choices=list(RemoteAccessType),
                    default=RemoteAccessType.JINAD,
                    type=RemoteAccessType.from_string,
                    help=f'the manager of remote Jina')

    gp.add_argument('--remote-quiet', action='store_true', default=False,
                    help=f'disable the streaming of remote logs on local')
