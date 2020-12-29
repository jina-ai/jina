from ..base import set_base_parser
from .login import set_hub_login_parser


def set_hub_list_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    set_hub_login_parser(parser)

    parser.add_argument('--name', type=str,
                        help='name of hub image')
    parser.add_argument('--kind', type=str,
                        help='kind of hub image')
    parser.add_argument('--keywords', type=str, nargs='+', metavar='KEYWORD',
                        help='keywords for searching')
    parser.add_argument('--type', type=str, default='pod', choices=['pod', 'app'],
                        help='type of the hub image')
    parser.add_argument('--local-only', action='store_true', default=False,
                        help='list all local hub images on the current machine')
    return parser