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
    gp.add_argument('--name', type=str,
                    help='''
The name of this object.

This will be used in the following places:
- how you refer to this object in Python/YAML/CLI
- log message
- ...

When not given, then the default naming strategy will apply.
                    ''')

    gp.add_argument('--log-config', type=str,
                    default=resource_filename('jina',
                                              '/'.join(('resources', 'logging.default.yml'))),
                    help='The YAML config of the logger used in this object.')

    # hidden CLI used for internal only

    gp.add_argument('--identity', type=str, default=random_identity(),
                    help='A UUID string to represent the identity of this object'
                    if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp.add_argument('--hide-exc-info', action='store_true', default=False,
                    help='If set, then exception stack information to be added to the logging message, '
                         'useful in debugging')
