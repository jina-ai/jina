"""Argparser module for hub push"""

import argparse
import os

from ..helper import add_arg_group


def mixin_hub_push_parser(parser):
    """Add the arguments for hub push to the parser
    :param parser: the parser configure
    """

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    gp = add_arg_group(parser, title='Push')
    gp.add_argument(
        'path',
        type=dir_path,
        help='''
The content source to be shipped into a Jina Hub executor. It can one of the followings:
- a directory containing Dockerfile, manifest.yml, README.md, zero or more yaml config, zero or more Python file.
''',
    )

    gp.add_argument(
        '-f',
        '--docker-file',
        metavar='PATH',
        help='Name of the Dockerfile (Default is `path/Dockerfile`)',
    )

    gp.add_argument(
        '-t',
        '--tag',
        action='append',
        help='Name and optionally a list of tags',
    )

    gp.add_argument(
        '--force',
        type=str,
        help='To overwrite the executor identified as UUID8',
    )
    gp.add_argument(
        '--secret',
        type=str,
        help='The secret key of the identified Jina Hub executor',
    )

    gp = add_arg_group(parser, title='Visibility')

    mutually_exclusive_group = gp.add_mutually_exclusive_group()

    mutually_exclusive_group.add_argument(
        '--public',
        action='store_true',
        default=argparse.SUPPRESS,
        help='If set, the pushed executor is visible to public',
    )

    mutually_exclusive_group.add_argument(
        '--private',
        action='store_true',
        default=argparse.SUPPRESS,
        help='If set, the pushed executor is invisible to public',
    )
