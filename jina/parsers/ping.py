from .base import set_base_parser


def set_ping_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('host', type=str,
                        help='host address of the target pod/pea, e.g. 0.0.0.0')
    parser.add_argument('port', type=int,
                        help='the control port of the target pod/pea')
    parser.add_argument('--timeout', type=int, default=3000,
                        help='timeout (ms) of one check, -1 for waiting forever')
    parser.add_argument('--retries', type=int, default=3,
                        help='max number of tried health checks before exit 1')
    parser.add_argument('--print-response', action='store_true', default=False,
                        help='print the response when received')
    return parser
