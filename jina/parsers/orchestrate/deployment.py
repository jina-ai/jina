"""Argparser module for Deployment runtimes"""
import argparse

from jina.enums import DeploymentRoleType
from jina.parsers.helper import _SHOW_ALL_ARGS, add_arg_group


def mixin_base_deployment_parser(parser):
    """Add mixin arguments required by :class:`BaseDeployment` into the given parser.

    :param parser: the parser instance to which we add arguments
    """
    gp = add_arg_group(parser, title='Deployment')

    gp.add_argument(
        '--uses-before',
        type=str,
        help='The executor attached after the Pods described by --uses, typically before sending to all '
        'shards, accepted type follows `--uses`',
    )
    gp.add_argument(
        '--uses-after',
        type=str,
        help='The executor attached after the Pods described by --uses, typically used for receiving from '
        'all shards, accepted type follows `--uses`',
    )

    gp.add_argument(
        '--external',
        action='store_true',
        default=False,
        help='The Deployment will be considered an external Deployment that has been started independently from the Flow.'
        'This Deployment will not be context managed by the Flow.',
    )

    # hidden CLI used for internal only

    gp.add_argument(
        '--deployment-role',
        type=DeploymentRoleType.from_string,
        choices=list(DeploymentRoleType),
        help='The role of this deployment in the flow'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
