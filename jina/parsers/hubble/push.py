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
        '--force',
        type=str,
        help='To overwrite the executor identified as UUID8',
    )
    gp.add_argument(
        '--secret',
        type=str,
        help='The secret key of the identified Jina Hub executor',
    )

    mutually_exclusive_group = parser.add_mutually_exclusive_group()

    from ...helper import colored

    mutually_exclusive_group.add_argument(
        '--public',
        action='store_true',
        default=False,
        help=f'''
        {colored('default: enabled', attrs=['dark'])}

        If set, the published executor is visible to public
        ''',
    )

    mutually_exclusive_group.add_argument(
        '--private',
        action='store_true',
        default=False,
        help='If set, the published executor is invisible to public',
    )
