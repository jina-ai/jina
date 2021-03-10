"""Argparser module for Optimizer"""
from .base import set_base_parser
from .peapods.base import mixin_base_ppr_parser
from typing import Optional

# noinspection PyUnreachableCode
if False:
    from argparse import ArgumentParser


def set_optimizer_parser(parser: Optional['ArgumentParser'] = None):
    """Set the parser for the optimizer

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()
    mixin_base_ppr_parser(parser)
    parser.add_argument(
        '--uses',
        type=str,
        help='The path to a YAML file which defines a FlowOptimizer.',
    )
    parser.add_argument(
        '--output-dir', type=str, help='The path to a YAML file to store the output.'
    )
    return parser
