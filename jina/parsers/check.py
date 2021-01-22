from .base import set_base_parser


def set_check_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--summary-exec', type=str,
                        help='The markdown file path for all executors summary')
    parser.add_argument('--summary-driver', type=str,
                        help='The markdown file path for all drivers summary')
    return parser
