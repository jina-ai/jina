"""Argparser module for Pea runtimes"""
import argparse

from ..helper import add_arg_group, _SHOW_ALL_ARGS, KVAppendAction
from ...enums import PeaRoleType, RuntimeBackendType
from ...peapods.runtimes import list_all_runtimes


def mixin_pea_parser(parser):
    """Mixing in arguments required by :class:`BasePea` into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='Pea')

    gp.add_argument(
        '--daemon',
        action='store_true',
        default=False,
        help='The Pea attempts to terminate all of its Runtime child processes/threads on existing. '
        'setting it to true basically tell the Pea do not wait on the Runtime when closing',
    )

    gp.add_argument(
        '--runtime-backend',
        '--runtime',
        type=RuntimeBackendType.from_string,
        choices=list(RuntimeBackendType),
        default=RuntimeBackendType.PROCESS,
        help='The parallel backend of the runtime inside the Pea',
    )

    gp.add_argument(
        '--runtime-cls',
        type=str,
        choices=list_all_runtimes(),
        default='ZEDRuntime',
        help='The runtime class to run inside the Pea',
    )

    gp.add_argument(
        '--timeout-ready',
        type=int,
        default=60000,
        help='The timeout in milliseconds of a Pea waits for the runtime to be ready, -1 for waiting '
        'forever',
    )

    gp.add_argument(
        '--env',
        action=KVAppendAction,
        metavar='KEY=VALUE',
        nargs='*',
        help='The map of environment variables that are available inside runtime',
    )

    gp.add_argument(
        '--expose-public',
        action='store_true',
        default=False,
        help='If set, expose the public IP address to remote when necessary, by default it exposes'
        'private IP address, which only allows accessing under the same network/subnet. Important to '
        'set this to true when the Pea will receive input connections from remote Peas',
    )

    # hidden CLI used for internal only

    gp.add_argument(
        '--pea-id',
        type=int,
        default=0,
        help='defines the suffix for the workspace path of the pea`'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--pea-role',
        type=PeaRoleType.from_string,
        choices=list(PeaRoleType),
        default=PeaRoleType.SINGLETON,
        help='The role of this Pea in a Pod' if _SHOW_ALL_ARGS else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--noblock-on-start',
        action='store_true',
        default=False,
        help='If set, starting a Pea/Pod does not block the thread/process. It then relies on '
        '`wait_start_success` at outer function for the postpone check.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
