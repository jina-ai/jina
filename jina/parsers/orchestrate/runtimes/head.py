import argparse

from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS


def mixin_head_parser(parser):
    """Mixing in arguments required by head pods and runtimes into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='Head')

    gp.add_argument(
        '--uses-before-address',
        type=str,
        help='The address of the uses-before runtime',
    )

    gp.add_argument(
        '--uses-after-address',
        type=str,
        help='The address of the uses-before runtime',
    )

    gp.add_argument(
        '--connection-list',
        type=str,
        help='dictionary JSON with a list of connections to configure',
    )

    gp.add_argument(
        '--disable-reduce',
        action='store_true',
        default=False,
        help='Disable the built-in reduce mechanism, set this if the reduction is to be handled by the Executor connected to this Head',
    )
