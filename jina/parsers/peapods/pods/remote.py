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

    gp.add_argument('--silent-remote-logs', action='store_true', default=False,
                    help=f'do not display the streaming of remote logs on local console')

    gp.add_argument('--upload-files', type=str, nargs='*', metavar='FILE',
                    help='the files on the host to be uploaded to the remote workspace. This can be useful when your '
                         'Pod has more file dependencies beyond a single YAML file, e.g. Python files, data files. '
                         'Note that currently only flatten structure is supported, which means if you upload '
                         '`[./foo/a.py, ./foo/b.pp, ./bar/c.yml]`, then they will be put under the _same_ workspace on '
                         'the remote, losing all hierarchies.')

