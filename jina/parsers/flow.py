"""Argparser module for Flow"""
from .base import set_base_parser
from .helper import add_arg_group, KVAppendAction


def mixin_flow_features_parser(parser):
    """Add the arguments for the Flow features to the parser

    :param parser: the parser configure
    """
    from ..enums import FlowInspectType

    gp = add_arg_group(parser, title='Flow Feature')

    gp.add_argument('--uses', type=str, help='The YAML file represents a flow')
    gp.add_argument(
        '--env',
        action=KVAppendAction,
        metavar='KEY=VALUE',
        nargs='*',
        help='The map of environment variables that are available inside runtime',
    )

    gp.add_argument(
        '--inspect',
        type=FlowInspectType.from_string,
        choices=list(FlowInspectType),
        default=FlowInspectType.COLLECT,
        help='''
    The strategy on those inspect pods in the flow.

    If `REMOVE` is given then all inspect pods are removed when building the flow.
    ''',
    )


def set_flow_parser(parser=None):
    """Set the parser for the flow

    :param parser: an (optional) initial parser to build upon
    :return: the parser
    """
    from .peapods.base import mixin_base_ppr_parser
    from .peapods.runtimes.remote import mixin_remote_parser
    from .client import mixin_client_type_parser, mixin_client_features_parser

    if not parser:
        parser = set_base_parser()

    mixin_base_ppr_parser(parser, with_identity=False)

    parser.set_defaults(workspace='./')

    mixin_remote_parser(parser)

    # add client parser
    mixin_client_type_parser(parser)
    mixin_client_features_parser(parser)

    mixin_flow_features_parser(parser)

    return parser
