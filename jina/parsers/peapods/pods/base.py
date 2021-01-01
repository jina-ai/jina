import argparse

from ...helper import add_arg_group, _SHOW_ALL_ARGS
from ....enums import PollingType, SchedulerType, RemoteAccessType, RemotePeapodType, PodRoleType


def mixin_base_pod_parser(parser):
    """Mixing in arguments required by :class:`BasePod` into the given parser. """
    gp = add_arg_group(parser, title='Pod')

    gp.add_argument('--uses-before', type=str,
                    help='the executor used before sending to all parallels, '
                         'accepted type follows "--uses"')
    gp.add_argument('--uses-after', type=str,
                    help='the executor used after receiving from all parallels, '
                         'accepted type follows "--uses"')

    gp.add_argument('--parallel', '--shards', type=int, default=1,
                    help='number of parallel peas in the pod running at the same time, '
                         '`port_in` and `port_out` will be set to random, '
                         'and routers will be added automatically when necessary')
    gp.add_argument('--polling', type=PollingType.from_string, choices=list(PollingType),
                    default=PollingType.ANY,
                    help='ANY: only one (whoever is idle) replica polls the message; '
                         'ALL: all workers poll the message (like a broadcast)')
    gp.add_argument('--scheduling', type=SchedulerType.from_string, choices=list(SchedulerType),
                    default=SchedulerType.LOAD_BALANCE,
                    help='the strategy of scheduling workload among peas')

    gp.add_argument('--remote-access', choices=list(RemoteAccessType),
                    default=RemoteAccessType.JINAD,
                    type=RemoteAccessType.from_string,
                    help=f'the way of managing remote runtime')
    gp.add_argument('--remote-type', choices=list(RemotePeapodType),
                    default=RemotePeapodType.POD,
                    type=RemotePeapodType.from_string,
                    help=f'the way of managing remote runtime')

    # hidden CLI used for internal only

    gp.add_argument('--pod-role', type=PodRoleType.from_string, choices=list(PodRoleType),
                    help='the role of this pod in the flow' if _SHOW_ALL_ARGS else argparse.SUPPRESS)
