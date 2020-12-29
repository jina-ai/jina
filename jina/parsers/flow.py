import argparse

from .base import set_base_parser
from .helper import add_arg_group, _SHOW_ALL_ARGS


def set_flow_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from ..enums import FlowOutputType, FlowOptimizeLevel, FlowInspectType
    from ..helper import get_random_identity

    gp = add_arg_group(parser, 'flow arguments')
    gp.add_argument('--uses', type=str, help='a yaml file represents a flow')
    from pkg_resources import resource_filename
    gp.add_argument('--logserver', action='store_true', default=False,
                    help='start a log server for the dashboard')
    gp.add_argument('--logserver-config', type=str,
                    default=resource_filename('jina',
                                              '/'.join(('resources', 'logserver.default.yml'))),
                    help='the yaml config of the log server')
    gp.add_argument('--log-id', type=str, default=get_random_identity(),
                    help='the log id used to aggregate logs by fluentd' if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp.add_argument('--optimize-level', type=FlowOptimizeLevel.from_string, default=FlowOptimizeLevel.NONE,
                    help='removing redundant routers from the flow. Note, this may change the gateway zmq socket to BIND \
                            and hence not allow multiple clients connected to the gateway at the same time.'
                    if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp.add_argument('--output-type', type=FlowOutputType.from_string,
                    choices=list(FlowOutputType), default=FlowOutputType.SHELL_PROC,
                    help='type of the output')
    gp.add_argument('--output-path', type=argparse.FileType('w', encoding='utf8'),
                    help='output path of the flow')
    gp.add_argument('--inspect', type=FlowInspectType.from_string,
                    choices=list(FlowInspectType), default=FlowInspectType.COLLECT,
                    help='strategy on those inspect pods in the flow. '
                         'if REMOVE is given then all inspect pods are removed when building the flow')
    return parser
