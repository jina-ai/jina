"""Argparser module for pinging"""
from jina.parsers.base import set_base_parser


def set_dryrun_parser(parser=None):
    """Set the parser for `dryrun`

    :param parser: an existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'host',
        type=str,
        help='The full host address of the Gateway, e.g. grpc://localhost:12345',
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=3000,
        help='''
Timeout in millisecond of one check
-1 for waiting forever
''',
    )

    return parser
