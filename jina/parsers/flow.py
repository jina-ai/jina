"""Argparser module for Flow"""
import argparse

from .base import set_base_parser
from .helper import _SHOW_ALL_ARGS
from .peapods.base import mixin_base_ppr_parser
from ..enums import FlowOptimizeLevel, FlowInspectType


def set_flow_parser(parser=None):
    """Set the parser for the flow

    :param parser: an (optional) initial parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    mixin_base_ppr_parser(parser)

    parser.add_argument('--uses', type=str, help='The YAML file represents a flow')
    parser.add_argument('--inspect', type=FlowInspectType.from_string,
                        choices=list(FlowInspectType), default=FlowInspectType.COLLECT,
                        help='''
The strategy on those inspect pods in the flow.

If `REMOVE` is given then all inspect pods are removed when building the flow.
''')

    parser.add_argument('--optimize-level', type=FlowOptimizeLevel.from_string, default=FlowOptimizeLevel.NONE,
                        help='removing redundant routers from the flow. Note, this may change the gateway zmq socket to BIND \
                            and hence not allow multiple clients connected to the gateway at the same time.'
                        if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    return parser
