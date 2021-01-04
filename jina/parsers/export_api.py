from .base import set_base_parser


def set_export_api_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--yaml-path', type=str, nargs='*', metavar='PATH',
                        help='the YAML file path for storing the exported API')
    parser.add_argument('--json-path', type=str, nargs='*', metavar='PATH',
                        help='the JSON file path for storing the exported API')
    return parser
