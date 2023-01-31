"""Extensive argparser module for logging"""


def mixin_suppress_root_logging_parser(parser):
    parser.add_argument(
        '--suppress-root-logging',
        action='store_true',
        default=False,
        help='If set, then no root handlers will be suppressed from logging.',
    )
