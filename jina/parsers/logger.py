from .base import set_base_parser


def set_logger_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--groupby-regex', type=str,
                        default=r'(.*@\d+)\[',
                        help='The regular expression for grouping logs')
    parser.add_argument('--refresh-time', type=int,
                        default=5,
                        help='The refresh time interval in seconds, set to -1 to persist all grouped logs')
    return parser
