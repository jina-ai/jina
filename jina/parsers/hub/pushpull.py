"""Argparser module for hub push & pull"""
from ..helper import add_arg_group


def mixin_hub_pushpull_parser(parser):
    """Add the arguments for hub push pull to the parser

    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='Push/Pull')
    gp.add_argument('name', type=str, help='The name of the image.')
    gp.add_argument(
        '--no-overwrite',
        action='store_true',
        default=False,
        help='If set, do not allow overwriting existing images (based on module version and jina version)',
    )


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
        '-f',
        '--file',
        type=str,
        default='Dockerfile',
        help='Name of the Dockerfile (Default is `Dockerfile`)',
    )
    gp.add_argument(
        '--private',
        action='store_true',
        default=False,
        help='If set, the published executor is invisible',
    )
    gp.add_argument(
        '--public',
        action='store_true',
        default=False,
        help='If set, the published executor is visible to public',
    )
    gp.add_argument(
        '--overwrite',
        type=str,
        default='',
        help='The access token of an existing Jina Hub executor',
    )
    gp.add_argument(
        '--secret',
        type=str,
        default='',
        help='The secret key of an existing Jina Hub executor',
    )
