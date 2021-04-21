"""Argparser module for Pod runtimes"""
import argparse

from jina.enums import PollingType, SchedulerType, PodRoleType
from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS, KVAppendAction


def mixin_base_pod_parser(parser):
    """Add mixin arguments required by :class:`BasePod` into the given parser.

    :param parser: the parser instance to which we add arguments
    """
    gp = add_arg_group(parser, title='Pod')

    gp.add_argument(
        '--uses-before',
        type=str,
        help='The executor attached after the Peas described by --uses, typically before sending to all '
        'parallels, accepted type follows `--uses`',
    )
    gp.add_argument(
        '--uses-after',
        type=str,
        help='The executor attached after the Peas described by --uses, typically used for receiving from '
        'all parallels, accepted type follows `--uses`',
    )
    gp.add_argument(
        '--parallel',
        '--shards',
        type=int,
        default=1,
        help='The number of parallel peas in the pod running at the same time, '
        '`port_in` and `port_out` will be set to random, '
        'and routers will be added automatically when necessary',
    )
    gp.add_argument(
        '--replicas',
        type=int,
        default=1,
        help='The number of replicas in the pod, '
        '`port_in` and `port_out` will be set to random, '
        'and routers will be added automatically when necessary',
    )
    gp.add_argument(
        '--polling',
        type=PollingType.from_string,
        choices=list(PollingType),
        default=PollingType.ANY,
        help='''
The polling strategy of the Pod (when `parallel>1`)
- ANY: only one (whoever is idle) Pea polls the message
- ALL: all Peas poll the message (like a broadcast)
''',
    )
    gp.add_argument(
        '--scheduling',
        type=SchedulerType.from_string,
        choices=list(SchedulerType),
        default=SchedulerType.LOAD_BALANCE,
        help='The strategy of scheduling workload among Peas',
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
    gp.add_argument(
        '--peas-hosts',
        nargs='+',
        type=str,
        help='''The hosts of the peas when parallel greater than 1.
        Peas will be evenly distributed among the hosts. By default,
        peas are running in the same host as the pod.''',
    )
