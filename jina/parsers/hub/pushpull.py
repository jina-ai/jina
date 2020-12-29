from .login import mixin_hub_login_parser
from ..base import set_base_parser


def set_hub_pushpull_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    mixin_hub_login_parser(parser)

    parser.add_argument('name', type=str, help='the name of the image.')
    return parser
