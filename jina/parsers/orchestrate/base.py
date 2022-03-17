"""Base argparser module for Pod and Deployment runtime"""
import argparse
import os

from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS
from jina.enums import PollingType
from jina.helper import random_identity


def mixin_base_ppr_parser(parser):
    """Mixing in arguments required by pod/deployment/runtime module into the given parser.
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
- ...

When not given, then the default naming strategy will apply.
                    ''',
    )

    gp.add_argument(
        '--workspace',
        type=str,
        default=None,
        help='The working directory for any IO operations in this object. '
        'If not set, then derive from its parent `workspace`.',
    )

    from jina import __resources_path__

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

    gp.add_argument(
        '--workspace-id',
        type=str,
        default=random_identity(),
        help='the UUID for identifying the workspace. When not given a random id will be assigned.'
        'Multiple Pod/Deployment/Flow will work under the same workspace if they share the same '
        '`workspace-id`.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    parser.add_argument(
        '--extra-search-paths',
        type=str,
        default=[],
        nargs='*',
        help='Extra search paths to be used when loading modules and finding YAML config files.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--timeout-ctrl',
        type=int,
        default=int(os.getenv('JINA_DEFAULT_TIMEOUT_CTRL', '60')),
        help='The timeout in milliseconds of the control request, -1 for waiting forever',
    )

    parser.add_argument(
        '--k8s-namespace',
        type=str,
        help='Name of the namespace where Kubernetes deployment should be deployed, to be filled by flow name'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--polling',
        type=str,
        default=PollingType.ANY.name,
        help='''
    The polling strategy of the Deployment and its endpoints (when `shards>1`).
    Can be defined for all endpoints of a Deployment or by endpoint.
    Define per Deployment:
    - ANY: only one (whoever is idle) Pod polls the message
    - ALL: all Pods poll the message (like a broadcast)
    Define per Endpoint:
    JSON dict, {endpoint: PollingType}
    {'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'}
    
    ''',
    )
