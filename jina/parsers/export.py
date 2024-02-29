"""Argparser module for the export API"""

from jina.parsers.base import set_base_parser
from jina.parsers.helper import _chf


def set_export_parser(parser=None):
    """Set the parser for exporting
    :param parser: the parser configure

    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    spp = parser.add_subparsers(
        dest='export',
        description='use `%(prog)-8s [sub-command] --help` '
        'to get detailed information about each sub-command',
        required=True,
    )

    set_export_flowchart_parser(
        spp.add_parser(
            'flowchart',
            help='Export a Flow YAML file to a flowchart',
            formatter_class=_chf,
        )
    )

    set_export_k8s_parser(
        spp.add_parser(
            'kubernetes',
            help='Export a Flow YAML file to a Kubernetes YAML bundle',
            formatter_class=_chf,
        )
    )

    set_export_docker_compose_parser(
        spp.add_parser(
            'docker-compose',
            help='Export a Flow YAML file to a Docker Compose YAML file',
            formatter_class=_chf,
        )
    )

    set_export_schema_parser(
        spp.add_parser(
            'schema',
            help='Export Jina Executor & Flow API to JSONSchema files',
            formatter_class=_chf,
        )
    )

    return parser


def mixin_base_io_parser(parser):
    """Add basic IO parsing args
    :param parser: the parser configure

    """
    parser.add_argument(
        'config_path',
        type=str,
        metavar='INPUT',
        help='The input file path of a Flow or Deployment YAML ',
    )
    parser.add_argument(
        'outpath',
        type=str,
        metavar='OUTPUT',
        help='The output path',
    )


def set_export_docker_compose_parser(parser=None):
    """Set the parser for the flow chart export

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    mixin_base_io_parser(parser)

    parser.add_argument(
        '--network_name',
        type=str,
        help='The name of the network that will be used by the deployment name.',
    )
    return parser


def set_export_k8s_parser(parser=None):
    """Set the parser for the flow chart export

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    mixin_base_io_parser(parser)

    parser.add_argument(
        '--k8s-namespace',
        type=str,
        help='The name of the k8s namespace to set for the configurations. If None, the name of the Flow will be used.',
    )
    return parser


def set_export_flowchart_parser(parser=None):
    """Set the parser for the flow chart export

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    mixin_base_io_parser(parser)

    parser.add_argument(
        '--vertical-layout',
        action='store_true',
        default=False,
        help='If set, then the flowchart is rendered vertically from top to down.',
    )
    return parser


def set_export_schema_parser(parser=None):
    """Set the parser for the API export

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        '--yaml-path',
        type=str,
        nargs='*',
        metavar='PATH',
        help='The YAML file path for storing the exported API',
    )
    parser.add_argument(
        '--json-path',
        type=str,
        nargs='*',
        metavar='PATH',
        help='The JSON file path for storing the exported API',
    )
    parser.add_argument(
        '--schema-path',
        type=str,
        nargs='*',
        metavar='PATH',
        help='The JSONSchema file path for storing the exported API',
    )
    return parser
