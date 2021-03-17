"""Argparser module for hub list"""
from ..helper import add_arg_group


def mixin_hub_list_parser(parser):
    """Add the arguments for hub list to the parser

    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='List')
    gp.add_argument('--name', type=str, help='The name of hub image')
    gp.add_argument('--kind', type=str, help='The kind of hub image')
    gp.add_argument(
        '--keywords',
        type=str,
        nargs='+',
        metavar='KEYWORD',
        help='The keywords for searching',
    )
    gp.add_argument(
        '--type',
        type=str,
        default='pod',
        choices=['pod', 'app'],
        help='The type of the hub image',
    )
    gp.add_argument(
        '--local-only',
        action='store_true',
        default=False,
        help='If set, list all local hub images on the current machine',
    )
