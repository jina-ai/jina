"""Argparser module for Pod runtimes"""
import argparse

from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS, KVAppendAction
from jina.enums import PodRoleType, RuntimeBackendType


def mixin_pod_parser(parser):
    """Mixing in arguments required by :class:`Pod` into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='Pod')

    gp.add_argument(
        '--daemon',
        action='store_true',
        default=False,
        help='The Pod attempts to terminate all of its Runtime child processes/threads on existing. '
        'setting it to true basically tell the Pod do not wait on the Runtime when closing',
    )

    gp.add_argument(
        '--runtime-backend',
        '--runtime',
        type=RuntimeBackendType.from_string,
        choices=list(RuntimeBackendType),
        default=RuntimeBackendType.PROCESS,
        help='The parallel backend of the runtime inside the Pod',
    )

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

    gp.add_argument(
        '--expose-public',
        action='store_true',
        default=False,
        help='If set, expose the public IP address to remote when necessary, by default it exposes'
        'private IP address, which only allows accessing under the same network/subnet. Important to '
        'set this to true when the Pod will receive input connections from remote Pods',
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
        '--replica-id',
        type=int,
        default=0,
        help='the id of the replica of an executor'
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
        'https://docs.jina.ai/fundamentals/flow/topology/',
    )

    gp.add_argument(
        '--replicas',
        type=int,
        default=1,
        help='The number of replicas in the deployment',
    )
