"""Extensive argparser module for logging"""


def mixin_suppress_root_logging_parser(parser):
    """Mixing in arguments required by every module into the given parser.
    This parser extends logging-related arguments.
    :param parser: the parser instance to which we add arguments
    """
    parser.add_argument(
        '--suppress-root-logging',
        action='store_true',
        default=False,
        help='If set, then no root handlers will be suppressed from logging.',
    )
