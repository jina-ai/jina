"""Module for argparse for Client"""
from .helper import add_arg_group


def mixin_client_cli_parser(parser):
    """Add the arguments for the client to the parser

    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='Client')

    gp.add_argument(
        '--request-size',
        type=int,
        default=100,
        help='The number of Documents in each Request.',
    )

    gp.add_argument('--mime-type', type=str, help='MIME type of the input Documents.')
    gp.add_argument(
        '--continue-on-error',
        action='store_true',
        default=False,
        help='If set, a Request that causes error will be logged only without blocking the further '
        'requests.',
    )
    gp.add_argument(
        '--return-results',
        action='store_true',
        default=False,
        help='''
This feature is only used for AsyncClient.

If set, the results of all Requests will be returned as a list. This is useful when one wants 
process Responses in bulk instead of using callback. 
                    ''',
    )
