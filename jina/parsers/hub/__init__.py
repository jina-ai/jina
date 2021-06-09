from ..base import set_base_parser


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
