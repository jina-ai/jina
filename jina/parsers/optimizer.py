from .base import set_base_parser
from .peapods.base import mixin_base_ppr_parser


def set_optimizer_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    mixin_base_ppr_parser(parser)
    parser.add_argument('--uses', type=str, help='a yaml file represents a optimizer')

    return parser
