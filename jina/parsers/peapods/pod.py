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
        'shards, accepted type follows `--uses`',
    )
    gp.add_argument(
        '--uses-after',
        type=str,
        help='The executor attached after the Peas described by --uses, typically used for receiving from '
        'all shards, accepted type follows `--uses`',
    )
    gp.add_argument(
        '--shards',
        '--parallel',
        type=int,
        default=1,
        help='The number of shards in the pod running at the same time, '
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
The polling strategy of the Pod (when `shards>1`)
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

    parser.add_argument(
        '--no-dynamic-routing',
        action='store_false',
        dest='dynamic_routing',
        default=True,
        help='The Pod will setup the socket types of the HeadPea and TailPea depending on this argument.',
    )

    parser.add_argument(
        '--connect-to-predecessor',
        action='store_true',
        default=False,
        help='The head Pea of this Pod will connect to the TailPea of the predecessor Pod.',
    )


def mixin_k8s_pod_parser(parser):
    """Add mixin arguments required by :class:`K8sPod` into the given parser.

    :param parser: the parser instance to which we add arguments
    """
    parser.add_argument(
        '--k8s-uses-init',
        type=str,
        # default='',
        help='Init container for k8s pod. Usually retrieves some data which or waits until some condition is fulfilled.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
    parser.add_argument(
        '--k8s-mount-path',
        type=str,
        # default='',
        help='Path where the init container and the executor can exchange files.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
    parser.add_argument(
        '--k8s-init-container-command',
        type=str,
        nargs='+',
        help='Arguments for the init container.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    parser.add_argument(
        '--k8s-custom-resource-dir',
        type=str,
        default=None,
        help='Path to a folder containing custom k8s template files which shall be used for this pod.'
        'Please copy the standard Jina resource files and add parameters as you need'
        ' to make sure the minimum configuration Jina needs is present'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
