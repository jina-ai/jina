"""Argparser module for hub push"""

import argparse
import os

from jina.parsers.helper import add_arg_group


def mixin_hub_push_parser(parser):
    """Add the arguments for hub push to the parser
    :param parser: the parser configure
    """

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='If set, more information will be printed.',
    )

    gp = add_arg_group(parser, title='Push')
    gp.add_argument(
        'path',
        type=dir_path,
        help='The Executor folder to be pushed to Jina Hub',
    )

    gp.add_argument(
        '-f',
        '--dockerfile',
        metavar='DOCKERFILE',
        help='The file path to the Dockerfile (default is `${cwd}/Dockerfile`)',
    )

    gp.add_argument(
        '-t',
        '--tag',
        action='append',
        help='''
A list of tags. One can use it to distinguish architecture (e.g. `cpu`, `gpu`) or versions (e.g. `v1`, `v2`).

One can later fetch a tagged Executor via `jinahub[+docker]://MyExecutor/gpu`
''',
    )

    gp.add_argument(
        '--force-update',
        '--force',
        type=str,
        help='If set, push will overwrite the Executor on the Hub that shares the same NAME or UUID8 identifier',
    )
    gp.add_argument(
        '--secret',
        type=str,
        help='The secret for overwrite a Hub executor',
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
