"""Argparser module for hub push"""
from ..helper import add_arg_group


def mixin_hub_push_parser(parser):
    """Add the arguments for hub push to the parser
    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='Push')
    gp.add_argument(
        'path',
        type=str,
        help='''
The content source to be shipped into a Jina Hub executor. It can one of the followings:
- a directory containing Dockerfile, manifest.yml, README.md, zero or more yaml config, zero or more Python file.
''',
    )
    gp.add_argument(
        '--private',
        action='store_true',
        default=False,
        help='If set, the published executor is invisible to public',
    )
    gp.add_argument(
        '--public',
        action='store_true',
        default=True,
        help='If set, the published executor is visible to public',
    )
    gp.add_argument(
        '--force',
        type=str,
        default='',
        help='To overwrite the executor identified as UUID8',
    )
    gp.add_argument(
        '--secret',
        type=str,
        default='',
        help='The secret key of the identified Jina Hub executor',
    )
