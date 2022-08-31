"""Argparser module for hub new"""

from jina.parsers.helper import add_arg_group


def mixin_hub_new_parser(parser):
    """Add the arguments for hub new to the parser
    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='Create Executor')
    gp.add_argument(
        '--name',
        help='the name of the Executor',
        type=str,
    )

    gp.add_argument(
        '--path',
        help='the path to store the Executor',
        type=str,
    )

    gp.add_argument(
        '--advance-configuration',
        help='If set, always set up advance configuration like description, keywords and url',
        action='store_true',
    )

    gp.add_argument(
        '--description',
        help='the short description of the Executor',
        type=str,
    )

    gp.add_argument(
        '--keywords',
        help='some keywords to help people search your Executor (separated by comma)',
        type=str,
    )

    gp.add_argument(
        '--url',
        help='the URL of your GitHub repo',
        type=str,
    )

    gp.add_argument(
        '--dockerfile',
        help='The Dockerfile template to use for the Executor',
        type=str,
        choices=['cpu', 'tf-gpu', 'torch-gpu', 'jax-gpu'],
    )
