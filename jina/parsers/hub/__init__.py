from ..base import set_base_parser
from ..helper import _chf


def set_hub_pushpull_parser(parser=None):
    """Set the parser for the hub push or hub pull

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    from .login import mixin_hub_docker_login_parser
    from .pushpull import mixin_hub_pushpull_parser

    mixin_hub_docker_login_parser(parser)
    mixin_hub_pushpull_parser(parser)
    return parser


def set_hub_build_parser(parser=None):
    """Set the parser for `hub build`

    :param parser: the parser configure
    :return: the new parser
    """
    if not parser:
        parser = set_base_parser()

    from .login import mixin_hub_docker_login_parser
    from .build import mixin_hub_build_parser

    mixin_hub_docker_login_parser(parser)
    mixin_hub_build_parser(parser)

    return parser


def set_hub_list_parser(parser=None):
    """Set the parser for `hub list`

    :param parser: the parser configure
    :return: the new parser
    """
    if not parser:
        parser = set_base_parser()

    from .list import mixin_hub_list_parser
    mixin_hub_list_parser(parser)

    return parser


def set_hub_new_parser(parser=None):
    """Set the parser for the `hub new` command

    :param parser: the parser configure
    :return: the new parser
    """
    if not parser:
        parser = set_base_parser()

    from .new import mixin_hub_new_parser
    mixin_hub_new_parser(parser)

    return parser


def set_hub_parser(parser=None):
    """Set the parser for the hub

    :param parser: the parser configure
    """
    if not parser:
        parser = set_base_parser()

    spp = parser.add_subparsers(dest='hub',
                                description='use `%(prog)-8s [sub-command] --help` '
                                            'to get detailed information about each sub-command', required=True)

    spp.add_parser('login', help='login via Github to push images to Jina hub registry',
                   description='Login via Github to push images to Jina hub registry',
                   formatter_class=_chf)

    set_hub_new_parser(
        spp.add_parser('new', aliases=['init', 'create'], help='create a new Hub executor or app using cookiecutter',
                       description='Create a new Hub executor or app using cookiecutter',
                       formatter_class=_chf))

    set_hub_build_parser(
        spp.add_parser('build', help='build a directory into Jina hub image',
                       description='Build a directory into Jina hub image',
                       formatter_class=_chf))

    set_hub_pushpull_parser(
        spp.add_parser('push', help='push an image to the Jina hub registry',
                       description='Push an image to the Jina hub registry',
                       formatter_class=_chf))

    set_hub_pushpull_parser(
        spp.add_parser('pull', help='pull an image from the Jina hub registry to local',
                       description='Pull an image to the Jina hub registry to local',
                       formatter_class=_chf))

    set_hub_list_parser(
        spp.add_parser('list', help='list hub executors from jina hub registry',
                       description='List hub executors from jina hub registry',
                       formatter_class=_chf))
