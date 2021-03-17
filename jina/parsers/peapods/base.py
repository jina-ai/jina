"""Base argparser module for Pea and Pod runtime"""
import argparse

from pkg_resources import resource_filename

from ..helper import add_arg_group, _SHOW_ALL_ARGS
from ...helper import random_identity


def mixin_base_ppr_parser(parser):
    """Mixing in arguments required by pea/pod/runtime module into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='Essential')
    gp.add_argument(
        '--name',
        type=str,
        help='''
The name of this object.

This will be used in the following places:
- how you refer to this object in Python/YAML/CLI
- visualization
- log message header
- automatics docs UI
- ...

When not given, then the default naming strategy will apply. 
                    ''',
    )

    gp.add_argument(
        '--description',
        type=str,
        help='The description of this object. It will be used in automatics docs UI.',
    )

    gp.add_argument(
        '--log-config',
        type=str,
        default=resource_filename(
            'jina', '/'.join(('resources', 'logging.default.yml'))
        ),
        help='The YAML config of the logger used in this object.',
    )

    gp.add_argument(
        '--quiet',
        action='store_true',
        default=False,
        help='If set, then no log will be emitted from this object.',
    )

    gp.add_argument(
        '--quiet-error',
        action='store_true',
        default=False,
        help='If set, then exception stack information will not be added to the log',
    )

    # hidden CLI used for internal only

    gp.add_argument(
        '--identity',
        type=str,
        default=random_identity(),
        help='A UUID string to represent the logger identity of this object'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
