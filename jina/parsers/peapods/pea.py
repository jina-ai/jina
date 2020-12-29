import argparse

from ..base import set_base_parser
from ..helper import add_arg_group, _SHOW_ALL_ARGS, KVAppendAction
from ...enums import PeaRoleType


def mixin_pea_parser(parser=None):
    """Mixing in arguments required by :class:`BasePea` into the given parser.
    """
    if not parser:
        parser = set_base_parser()

    gp0 = add_arg_group(parser, title='Pea')

    gp0.add_argument('--daemon', action='store_true', default=False,
                     help='when a Runtime exits, it attempts to terminate all of its daemonic child processes. '
                          'setting it to true basically tell the Pea do not wait on the Runtime when closing')
    gp0.add_argument('--runtime-backend', '--runtime',
                     type=str, choices=['thread', 'process'], default='process',
                     help='the parallel backend of the runtime')
    gp0.add_argument('--runtime-cls', type=str, choices=['thread', 'process'], default='process',
                     help='the runtime class to equip')

    gp0.add_argument('--timeout-ready', type=int, default=10000,
                     help='timeout (ms) of a pea waits for the runtime to be ready, -1 for waiting forever')

    gp0.add_argument('--env', action=KVAppendAction,
                     metavar='KEY=VALUE', nargs='*',
                     help='a map of environment variables that are available inside runtime.')

    gp0.add_argument('--expose-public', action='store_true', default=False,
                     help='expose the public IP address to remote when necessary, by default it exposes'
                          'private IP address, which only allows accessing under the same network/subnet')

    gp0.add_argument('--pea-id', type=int, default=-1,
                     help='the id of the storage of this pea, only effective when `separated_workspace=True`'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp0.add_argument('--role', type=PeaRoleType.from_string, choices=list(PeaRoleType),
                     help='the role of this pea in a pod' if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    return parser
