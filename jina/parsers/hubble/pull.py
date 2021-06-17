"""Argparser module for hub push"""
from ..helper import add_arg_group


def mixin_hub_pull_parser(parser):
    """Add the arguments for hub pull to the parser
    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='Pull')
    gp.add_argument(
        'id',
        type=str,
        help='The UUID8 of the executor to download',
    )
    gp.add_argument(
        '--docker',
        action='store_true',
        default=False,
        help='If set, pull the Docker image from the Jina Hub registry',
    )
    gp.add_argument(
        '--secret',
        type=str,
        help='The secret key of the identified Jina Hub executor',
    )
