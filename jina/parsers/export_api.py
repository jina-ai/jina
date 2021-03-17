"""Argparser module for the export API"""
from .base import set_base_parser


def set_export_api_parser(parser=None):
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
