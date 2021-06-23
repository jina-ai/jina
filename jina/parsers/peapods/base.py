"""Base argparser module for Pea and Pod runtime"""
import argparse
import os

from ..helper import add_arg_group, _SHOW_ALL_ARGS
from ...helper import random_identity


def mixin_base_ppr_parser(parser, with_identity: bool = True):
    """Mixing in arguments required by pea/pod/runtime module into the given parser.
    :param parser: the parser instance to which we add arguments
    :param with_identity: if to include identity in the parser
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
- ...

When not given, then the default naming strategy will apply.
                    ''',
    )

    gp.add_argument(
        '--workspace',
        type=str,
        help='The working directory for any IO operations in this object. '
        'If not set, then derive from its parent `workspace`.',
    )

    from ... import __resources_path__

    gp.add_argument(
        '--log-config',
        type=str,
        default=os.path.join(__resources_path__, 'logging.default.yml'),
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
    if with_identity:
        gp.add_argument(
            '--identity',
            type=str,
            default=random_identity(),
            help='A UUID string to represent the logger identity of this object'
            if _SHOW_ALL_ARGS
            else argparse.SUPPRESS,
        )

    gp.add_argument(
        '--workspace-id',
        type=str,
        default=random_identity(),
        help='the UUID for identifying the workspace. When not given a random id will be assigned.'
        'Multiple Pea/Pod/Flow will work under the same workspace if they share the same '
        '`workspace-id`.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
