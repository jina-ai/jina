"""Argparser module for Pod runtimes"""
import argparse

from jina import __default_port_monitoring__, helper
from jina.enums import PodRoleType
from jina.parsers.helper import _SHOW_ALL_ARGS, KVAppendAction, add_arg_group


def mixin_pod_parser(parser):
    """Mixing in arguments required by :class:`Pod` into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='Pod')

    gp.add_argument(
        '--runtime-cls',
        type=str,
        default='WorkerRuntime',
        help='The runtime class to run inside the Pod',
    )

    gp.add_argument(
        '--timeout-ready',
        type=int,
        default=600000,
        help='The timeout in milliseconds of a Pod waits for the runtime to be ready, -1 for waiting '
        'forever',
    )

    gp.add_argument(
        '--env',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='The map of environment variables that are available inside runtime',
    )

    # hidden CLI used for internal only

    gp.add_argument(
        '--shard-id',
        type=int,
        default=0,
        help='defines the shard identifier for the executor. It is used as suffix for the workspace path of the executor`'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--pod-role',
        type=PodRoleType.from_string,
        choices=list(PodRoleType),
        default=PodRoleType.WORKER,
        help='The role of this Pod in a Deployment'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--noblock-on-start',
        action='store_true',
        default=False,
        help='If set, starting a Pod/Deployment does not block the thread/process. It then relies on '
        '`wait_start_success` at outer function for the postpone check.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--shards',
        type=int,
        default=1,
        help='The number of shards in the deployment running at the same time. For more details check '
        'https://docs.jina.ai/fundamentals/flow/create-flow/#complex-flow-topologies',
    )

    gp.add_argument(
        '--replicas',
        type=int,
        default=1,
        help='The number of replicas in the deployment',
    )

    gp.add_argument(
        '--port',
        type=int,
        default=helper.random_port(),
        help='The port for input data to bind to, default is a random port between [49152, 65535]',
    )

    gp.add_argument(
        '--monitoring',
        action='store_true',
        default=False,
        help='If set, spawn an http server with a prometheus endpoint to expose metrics',
    )

    gp.add_argument(
        '--port-monitoring',
        type=int,
        default=__default_port_monitoring__,  # default prometheus server port
        dest='port_monitoring',
        help=f'The port on which the prometheus server is exposed, default port is {__default_port_monitoring__} ',
    )
