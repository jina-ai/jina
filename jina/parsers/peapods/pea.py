import argparse

from ..helper import add_arg_group, _SHOW_ALL_ARGS, KVAppendAction
from ...enums import PeaRoleType, RuntimeBackendType
from ...peapods.runtimes import list_all_runtimes


def mixin_pea_parser(parser):
    """Mixing in arguments required by :class:`BasePea` into the given parser.
    """

    gp = add_arg_group(parser, title='Pea')

    gp.add_argument('--daemon', action='store_true', default=False,
                    help='the Pea attempts to terminate all of its Runtime child processes/threads on existing. '
                         'setting it to true basically tell the Pea do not wait on the Runtime when closing')

    gp.add_argument('--runtime-backend', '--runtime',
                    type=RuntimeBackendType.from_string,
                    choices=list(RuntimeBackendType),
                    default=RuntimeBackendType.PROCESS,
                    help='the parallel backend of the runtime inside the pea')

    gp.add_argument('--runtime-cls', type=str, choices=list_all_runtimes(), default='ZEDRuntime',
                    help='the runtime class to run inside the pea')

    gp.add_argument('--timeout-ready', type=int, default=10000,
                    help='timeout (ms) of a pea waits for the runtime to be ready, -1 for waiting forever')

    gp.add_argument('--env', action=KVAppendAction,
                    metavar='KEY=VALUE', nargs='*',
                    help='a map of environment variables that are available inside runtime')

    gp.add_argument('--expose-public', action='store_true', default=False,
                    help='expose the public IP address to remote when necessary, by default it exposes'
                         'private IP address, which only allows accessing under the same network/subnet')

    # hidden CLI used for internal only

    gp.add_argument('--pea-id', type=int, default=-1,
                    help='the id of the storage of this pea, only effective when `separated_workspace=True`'
                    if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp.add_argument('--pea-role', type=PeaRoleType.from_string, choices=list(PeaRoleType),
                    default=PeaRoleType.SINGLETON,
                    help='the role of this pea in a pod' if _SHOW_ALL_ARGS else argparse.SUPPRESS)
