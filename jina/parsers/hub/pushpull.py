"""Argparser module for hub push & pull"""
from ..helper import add_arg_group


def mixin_hub_pushpull_parser(parser):
    """Add the arguments for hub push pull to the parser

    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='Push/Pull')
    gp.add_argument('name', type=str, help='The name of the image.')
    gp.add_argument('--no-overwrite', action='store_true', default=False,
                    help='If set, do not allow overwriting existing images (based on module version and jina version)')
