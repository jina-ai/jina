"""Argparser module for the check functions"""
from .base import set_base_parser


def set_check_parser(parser=None):
    """Set the `check` parser

    :param parser: an optional existing parser to build upon
    :return: parser
    """
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        '--summary-exec',
        type=str,
        help='The markdown file path for all executors summary',
    )
    return parser
