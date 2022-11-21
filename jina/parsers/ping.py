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
        help='The target type to ping. For `executor` and `gateway`, checks the readiness of the individual service. '
             'For `flow` it checks the connectivity of the complete microservice architecture.',
        default='executor',
    )

    parser.add_argument(
        'host',
        type=str,
        help='The host address with port of a target Executor, Gateway or a Flow, e.g. 0.0.0.0:8000. For Flow or Gateway, host can also indicate the protocol, grpc will be used if not provided, e.g http://0.0.0.0:8000',
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
        '--attempts',
        type=int,
        default=1,
        help='The number of readiness checks to perform',
    )
    parser.add_argument(
        '--min-successful-attempts',
        type=int,
        default=1,
        help='The minimum number of successful readiness checks, before exiting successfully with exit(0)',
    )
    return parser
