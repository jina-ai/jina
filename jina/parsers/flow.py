"""Argparser module for Flow"""
from .base import set_base_parser
from .peapods.base import mixin_base_ppr_parser
from ..enums import FlowInspectType


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

    return parser
