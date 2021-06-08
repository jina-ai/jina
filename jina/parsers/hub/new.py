"""Argparser module for hub new"""
from ..helper import add_arg_group


def mixin_hub_new_parser(parser):
    """Add the options for `hub new` to the parser
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Create')

    gp.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='where to output the generated project dir into.',
    )
    gp.add_argument(
        '--overwrite',
        action='store_true',
        default=False,
        help='overwrite the contents of output directory if it exists',
    )
