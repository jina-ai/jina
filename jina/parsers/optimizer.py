from .base import set_base_parser
from .peapods.base import mixin_base_ppr_parser

if False:
    from argparse import ArgumentParser


def set_optimizer_parser(parser: 'ArgumentParser' = None):
    if not parser:
        parser = set_base_parser()
    mixin_base_ppr_parser(parser)
    parser.add_argument('--uses', type=str, help='path to a yaml file which defines an optimizer')
    parser.add_argument('--output-dir', type=str, help='path to a yaml file to store the output')
    return parser
