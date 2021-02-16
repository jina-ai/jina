"""Argparser module for pinging"""
from .base import set_base_parser


def set_ping_parser(parser=None):
    """Set the parser for `ping`

    :param parser: an existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    parser.add_argument('host', type=str,
                        help='The host address of the target Pea, e.g. 0.0.0.0')
    parser.add_argument('port', type=int,
                        help='The control port of the target pod/pea')
    parser.add_argument('--timeout', type=int, default=3000,
                        help='''
Timeout in millisecond of one check
-1 for waiting forever
''')
    parser.add_argument('--retries', type=int, default=3,
                        help='The max number of tried health checks before exit with exit code 1')
    parser.add_argument('--print-response', action='store_true', default=False,
                        help='If set, print the response when received')
    return parser
