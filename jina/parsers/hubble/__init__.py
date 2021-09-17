from ..base import set_base_parser
from ..helper import _chf


def mixin_hub_usage_parser(parser):
    """Add the arguments for hub pull to the parser
    :param parser: the parser configure
    """
    parser.add_argument(
        '--no-usage',
        action='store_true',
        default=False,
        help='If set, Hub executor usage will not be printed.',
    )


def set_hub_push_parser(parser=None):
    """Set the parser for the hub push
    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    from .push import mixin_hub_push_parser

    mixin_hub_usage_parser(parser)
    mixin_hub_push_parser(parser)
    return parser


def set_hub_pull_parser(parser=None):
    """Set the parser for the hub pull
    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    from .pull import mixin_hub_pull_parser

    mixin_hub_usage_parser(parser)
    mixin_hub_pull_parser(parser)
    return parser


def set_hub_new_parser(parser=None):
    """Set the parser for the hub pull
    :param parser: an optional existing parser to build upon
    :return: the parser
    """

    parser.add_argument(
        '-n',
        '--name',
        help='Setup name of the executor',
        action='store',
        type=str,
        default=None,
    )

    parser.add_argument(
        '-p',
        '--path',
        help='Path to store an executor',
        action='store',
        type=str,
        default=None,
    )

    parser.add_argument(
        '-ac',
        '--advance_configuration',
        help='Set up advance configuration',
        choices=('True', 'False'),
        default=None,
    )

    parser.add_argument(
        '-d',
        '--description',
        help='Give a short description of your executor',
        type=str,
        default=None,
    )

    parser.add_argument(
        '-k',
        '--keywords',
        help='Give some keywords to help people search your executor(separated by space)',
        type=str,
        default=None,
    )

    parser.add_argument(
        '-u',
        '--url',
        help='URL of your GitHub repo',
        action='store',
        type=str,
        default=None,
    )

    parser.add_argument(
        '-ad',
        '--add_dockerfile',
        help='Set True to create your own docker file',
        choices=('True', 'False'),
        default=None,
    )
    return parser


def set_hub_parser(parser=None):
    """Set the parser for the hub
    :param parser: the parser configure

    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    spp = parser.add_subparsers(
        dest='hub',
        description='use `%(prog)-8s [sub-command] --help` '
        'to get detailed information about each sub-command',
        required=True,
    )

    sppp = spp.add_parser(
        'new',
        help='create a new executor using the template',
        description='Create a new executor using the template',
        formatter_class=_chf,
    )

    sppp.add_argument(
        '--name',
        help='Setup name of the executor',
        action='store',
        type=str,
        default=None,
    )

    sppp.add_argument(
        '--path',
        help='Path to store an executor',
        action='store',
        type=str,
        default=None,
    )

    sppp.add_argument(
        '--advance_config',
        help='Set up advance configuration',
        choices=('True', 'False'),
        default=None,
    )

    sppp.add_argument(
        '--description',
        help='Give a short description of your executor',
        type=str,
        default=None,
    )

    sppp.add_argument(
        '--keywords',
        help='Give some keywords to help people search your executor(separated by space)',
        type=str,
        default=None,
    )

    sppp.add_argument(
        '--url', help='URL of your GitHub repo', action='store', type=str, default=None
    )

    sppp.add_argument(
        '--is_dockerfile',
        help='Set up advance configuration',
        choices=('True', 'False'),
        default=None,
    )

    set_hub_push_parser(
        spp.add_parser(
            'push',
            help='push an executor package to Jina hub',
            description='Push an executor package to Jina hub',
            formatter_class=_chf,
        )
    )

    set_hub_pull_parser(
        spp.add_parser(
            'pull',
            help='download an executor image/package from Jina hub',
            description='Download an executor image/package from Jina hub',
            formatter_class=_chf,
        )
    )

    return parser
