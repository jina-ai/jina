"""Argparser module for Pod runtimes"""
import argparse
from dataclasses import dataclass
from typing import Dict

from jina import helper
from jina.enums import PodRoleType
from jina.parsers.helper import _SHOW_ALL_ARGS, KVAppendAction, add_arg_group


@dataclass
class PodTypeParams:
    """Data Class representing possible parameters for each pod type"""

    runtime_cls: str
    role_type: PodRoleType


POD_PARAMS_MAPPING: Dict[str, PodTypeParams] = {
    'worker': PodTypeParams(runtime_cls='WorkerRuntime', role_type=PodRoleType.WORKER),
    'head': PodTypeParams(runtime_cls='HeadRuntime', role_type=PodRoleType.HEAD),
    'gateway': PodTypeParams(
        runtime_cls='GatewayRuntime', role_type=PodRoleType.GATEWAY
    ),
}


def mixin_pod_parser(parser, pod_type: str = 'worker'):
    """Mixing in arguments required by :class:`Pod` into the given parser.
    :param parser: the parser instance to which we add arguments
    :param pod_type: the pod_type configured by the parser. Can be either 'worker' for WorkerRuntime or 'gateway' for GatewayRuntime
    """

    gp = add_arg_group(parser, title='Pod')

    gp.add_argument(
        '--runtime-cls',
        type=str,
        default=POD_PARAMS_MAPPING[pod_type].runtime_cls,
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
        default=POD_PARAMS_MAPPING[pod_type].role_type,
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
        '--port',
        type=str,
        default=str(helper.random_port()),
        help='The port for input data to bind to, default is a random port between [49152, 65535].'
        ' In the case of an external Executor (`--external` or `external=True`) this can be a list of ports, separated by commas.'
        ' Then, every resulting address will be considered as one replica of the Executor.',
    )

    gp.add_argument(
        '--monitoring',
        action='store_true',
        default=False,
        help='If set, spawn an http server with a prometheus endpoint to expose metrics',
    )

    gp.add_argument(
        '--port-monitoring',
        type=str,
        default=str(helper.random_port()),
        dest='port_monitoring',
        help=f'The port on which the prometheus server is exposed, default is a random port between [49152, 65535]',
    )

    gp.add_argument(
        '--retries',
        type=int,
        default=-1,
        dest='retries',
        help=f'Number of retries per gRPC call. If <0 it defaults to max(3, num_replicas)',
    )

    gp.add_argument(
        '--floating',
        action='store_true',
        default=False,
        help='If set, the current Pod/Deployment can not be further chained, '
        'and the next `.add()` will chain after the last Pod/Deployment not this current one.',
    )

    gp.add_argument(
        '--tracing',
        action='store_true',
        default=False,
        help='If set, the sdk implementation of the OpenTelemetry tracer will be available and will be enabled for automatic tracing of requests and customer span creation. '
        'Otherwise a no-op implementation will be provided.',
    )

    parser.add_argument(
        '--traces-exporter-host',
        type=str,
        default=None,
        help='If tracing is enabled, this hostname will be used to configure the trace exporter agent.',
    )

    parser.add_argument(
        '--traces-exporter-port',
        type=int,
        default=None,
        help='If tracing is enabled, this port will be used to configure the trace exporter agent.',
    )

    parser.add_argument(
        '--metrics',
        action='store_true',
        default=False,
        help='If set, the sdk implementation of the OpenTelemetry metrics will be available for default monitoring and custom measurements. '
        'Otherwise a no-op implementation will be provided.',
    )

    parser.add_argument(
        '--metrics-exporter-host',
        type=str,
        default=None,
        help='If tracing is enabled, this hostname will be used to configure the metrics exporter agent.',
    )

    parser.add_argument(
        '--metrics-exporter-port',
        type=int,
        default=None,
        help='If tracing is enabled, this port will be used to configure the metrics exporter agent.',
    )
