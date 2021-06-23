from ..base import set_base_parser
from ..helper import _chf


def set_hub_push_parser(parser=None):
    """Set the parser for the hub push
    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    from .push import mixin_hub_push_parser

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

    mixin_hub_pull_parser(parser)
    return parser


def set_hub_parser(parser=None):
    """Set the parser for the hub
    :param parser: the parser configure
    """
    if not parser:
        parser = set_base_parser()

    spp = parser.add_subparsers(
        dest='hub',
        description='use `%(prog)-8s [sub-command] --help` '
        'to get detailed information about each sub-command',
        required=True,
    )

    set_hub_push_parser(
        spp.add_parser(
            'push',
            help='push an executor package to the Jina hub',
            description='Push an executor package to the Jina hub',
            formatter_class=_chf,
        )
    )

    set_hub_pull_parser(
        spp.add_parser(
            'pull',
            help='download an executor package/image from the Jina hub',
            description='Download an executor package/image from the Jina hub',
            formatter_class=_chf,
        )
    )
