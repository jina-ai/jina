"""Argparser module for distributed runtimes"""
import argparse

from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS


def mixin_distributed_feature_parser(parser):
    """Mixing in arguments required by :class:`BasePod` into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='Distributed')

    gp.add_argument(
        '--quiet-remote-logs',
        action='store_true',
        default=False,
        help='Do not display the streaming of remote logs on local console',
    )

    gp.add_argument(
        '--upload-files',
        type=str,
        nargs='*',
        metavar='FILE',
        help='''
The files on the host to be uploaded to the remote
workspace. This can be useful when your Pod has more
file dependencies beyond a single YAML file, e.g.
Python files, data files.

Note,
- currently only flatten structure is supported, which means if you upload `[./foo/a.py, ./foo/b.pp, ./bar/c.yml]`, then they will be put under the _same_ workspace on the remote, losing all hierarchies.
- by default, `--uses` YAML file is always uploaded.
- uploaded files are by default isolated across the runs. To ensure files are submitted to the same workspace across different runs, use `--workspace-id` to specify the workspace.
''',
    )

    gp.add_argument(
        '--disable-remote',
        action='store_true',
        default=False,
        help='If set, remote pea invocation is avoided. This is used by peas created by JinaD'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
