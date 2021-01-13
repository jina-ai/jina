import argparse

from .base import set_base_parser
from .helper import _SHOW_ALL_ARGS
from ..enums import FlowOutputType, FlowOptimizeLevel, FlowInspectType
from ..helper import get_random_identity


def set_flow_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--uses', type=str, help='a yaml file represents a flow')
    parser.add_argument('--log-id', type=str, default=get_random_identity(),
                        help='the log id used to aggregate logs by fluentd' if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    parser.add_argument('--optimize-level', type=FlowOptimizeLevel.from_string, default=FlowOptimizeLevel.NONE,
                        help='removing redundant routers from the flow. Note, this may change the gateway zmq socket to BIND \
                            and hence not allow multiple clients connected to the gateway at the same time.'
                        if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    parser.add_argument('--output-type', type=FlowOutputType.from_string,
                        choices=list(FlowOutputType), default=FlowOutputType.SHELL_PROC,
                        help='type of the output')
    parser.add_argument('--output-path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the flow')
    parser.add_argument('--inspect', type=FlowInspectType.from_string,
                        choices=list(FlowInspectType), default=FlowInspectType.COLLECT,
                        help='strategy on those inspect pods in the flow. '
                             'if REMOVE is given then all inspect pods are removed when building the flow')
    return parser
