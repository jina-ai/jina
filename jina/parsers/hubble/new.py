"""Argparser module for hub new"""

import argparse

from ..helper import add_arg_group


def mixin_hub_new_parser(parser):
    """Add the arguments for hub new to the parser
    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='New')
    gp.add_argument(
        '--name',
        help='Setup name of the executor',
        type=str,
        default=None,
    )

    gp.add_argument(
        '--path',
        help='Path to store an executor',
        type=str,
        default=None,
    )

    gp.add_argument(
        '--advance-configuration',
        help='If set, always set up advance configuration like description, keywords and url',
        action='store_true',
    )

    gp.add_argument(
        '--description',
        help='Give a short description of your executor',
        type=str,
        default=None,
    )

    gp.add_argument(
        '--keywords',
        help='Give some keywords to help people search your executor(separated by space)',
        type=str,
        default=None,
    )

    gp.add_argument(
        '--url',
        help='URL of your GitHub repo',
        type=str,
        default=None,
    )

    gp.add_argument(
        '--add-dockerfile',
        help='If set, always creates your own docker file',
        action='store_true',
    )
