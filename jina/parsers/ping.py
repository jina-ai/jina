"""Argparser module for pinging"""
from jina.parsers.base import set_base_parser


def set_ping_parser(parser=None):
    """Set the parser for `ping`

    :param parser: an existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'target',
        type=str,
        choices=['flow', 'executor', 'gateway'],
        help='The target type to ping. For `executor` and `gateway`, checks the readiness of the individual service. For `flow` it checks the connectivity of the complete microservice architecture.',
        default='executor',
    )

    parser.add_argument(
        'host',
        type=str,
        help='The host address with port of a target Executor or a Flow, e.g. 0.0.0.0:8000',
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
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='The max number of tried health checks before exit with exit code 1',
    )
    parser.add_argument(
        '--protocol',
        type=str,
        default='grpc',
        help='The protocol used to serve the gateway which determines how readiness is checked. Options are: `grpc`, `http` and `websocket`. Defaults to `grpc`',
    )
    return parser
