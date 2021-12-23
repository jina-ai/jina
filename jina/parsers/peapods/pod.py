"""Argparser module for Pod runtimes"""
import argparse

from jina.enums import PodRoleType
from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS


def mixin_base_pod_parser(parser):
    """Add mixin arguments required by :class:`BasePod` into the given parser.

    :param parser: the parser instance to which we add arguments
    """
    gp = add_arg_group(parser, title='Pod')

    gp.add_argument(
        '--uses-before',
        type=str,
        help='The executor attached after the Peas described by --uses, typically before sending to all '
        'shards, accepted type follows `--uses`',
    )
    gp.add_argument(
        '--uses-after',
        type=str,
        help='The executor attached after the Peas described by --uses, typically used for receiving from '
        'all shards, accepted type follows `--uses`',
    )

    gp.add_argument(
        '--external',
        action='store_true',
        default=False,
        help='The Pod will be considered an external Pod that has been started independently from the Flow.'
        'This Pod will not be context managed by the Flow.',
    )

    gp.add_argument(
        '--peas-hosts',
        nargs='+',
        type=str,
        help='''The hosts of the peas when shards greater than 1.
        Peas will be evenly distributed among the hosts. By default,
        peas are running on host provided by the argument ``host``''',
    )

    # hidden CLI used for internal only

    gp.add_argument(
        '--pod-role',
        type=PodRoleType.from_string,
        choices=list(PodRoleType),
        help='The role of this pod in the flow'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
