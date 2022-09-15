"""Argparser module for hub query"""
import os

from jina.parsers.helper import add_arg_group


def mixin_hub_status_parser(parser):
    """Add the arguments for hub query to the parser
    :param parser: the parser configure
    """

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    gp = add_arg_group(parser, title='Status')
    gp.add_argument(
        'path',
        nargs='?',
        default='.',
        type=dir_path,
        help='The Executor folder to be pushed to Jina Hub.',
    )

    gp.add_argument(
        '--id',
        type=str,
        help='If set, you can get the specified building state of a pushed Executor.',
    )

    gp.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='If set, more building status information of a pushed Executor will be printed.',
    )

    gp.add_argument(
        '--replay',
        action='store_true',
        default=False,
        help='If set, history building status information of a pushed Executor will be printed.',
    )
