"""Argparser module for hub new"""

import argparse

from ..helper import add_arg_group


def mixin_hub_new_parser(parser):
    """Add the arguments for hub new to the parser
    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='New')
    gp.add_argument(
        '-n',
        '--name',
        help='Setup name of the executor',
        action='store',
        type=str,
        default=None,
    )

    gp.add_argument(
        '-p',
        '--path',
        help='Path to store an executor',
        action='store',
        type=str,
        default=None,
    )

    gp.add_argument(
        '-ac',
        '--advance_configuration',
        help='Set up advance configuration',
        choices=('True', 'False'),
        default=None,
    )

    gp.add_argument(
        '-d',
        '--description',
        help='Give a short description of your executor',
        type=str,
        default=None,
    )

    gp.add_argument(
        '-k',
        '--keywords',
        help='Give some keywords to help people search your executor(separated by space)',
        type=str,
        default=None,
    )

    gp.add_argument(
        '-u',
        '--url',
        help='URL of your GitHub repo',
        action='store',
        type=str,
        default=None,
    )

    gp.add_argument(
        '-ad',
        '--add_dockerfile',
        help='Set True to create your own docker file',
        choices=('True', 'False'),
        default=None,
    )
