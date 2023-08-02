"""Argparser module for Flow"""

from jina.parsers.base import set_base_parser
from jina.parsers.helper import KVAppendAction, add_arg_group
from jina.parsers.orchestrate.base import mixin_essential_parser
from jina.parsers.logging import mixin_suppress_root_logging_parser


def mixin_flow_features_parser(parser):
    """Add the arguments for the Flow features to the parser

    :param parser: the parser configure
    """
    from jina.enums import FlowInspectType

    gp = add_arg_group(parser, title='Flow Feature')

    gp.add_argument(
        '--uses',
        type=str,
        help='The YAML path represents a flow. It can be either a local file path or a URL.',
    )

    gp.add_argument(
        '--reload',
        action='store_true',
        default=False,
        help='If set, auto-reloading on file changes is enabled: the Flow will restart while blocked if  YAML '
        'configuration source is changed. This also applies apply to underlying Executors, if their source '
        'code or YAML configuration has changed.',
    )

    gp.add_argument(
        '--env',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='The map of environment variables that are available inside runtime',
    )

    gp.add_argument(
        '--inspect',
        type=FlowInspectType.from_string,
        choices=list(FlowInspectType),
        default=FlowInspectType.COLLECT,
        help='''
    The strategy on those inspect deployments in the flow.

    If `REMOVE` is given then all inspect deployments are removed when building the flow.
    ''',
    )


def set_flow_parser(parser=None):
    """Set the parser for the flow

    :param parser: an (optional) initial parser to build upon
    :return: the parser
    """

    if not parser:
        parser = set_base_parser()

    mixin_essential_parser(parser)
    mixin_suppress_root_logging_parser(parser)
    mixin_flow_features_parser(parser)

    return parser
