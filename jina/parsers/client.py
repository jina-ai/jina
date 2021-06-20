"""Module for argparse for Client"""
from .helper import add_arg_group


def mixin_comm_protocol_parser(parser):
    """Add the arguments for the protocol to the parser

    :param parser: the parser configure
    """

    from ..enums import GatewayProtocolType

    parser.add_argument(
        '--protocol',
        type=GatewayProtocolType.from_string,
        choices=list(GatewayProtocolType),
        default=GatewayProtocolType.GRPC,
        help='Communication protocol between server and client.',
    )


def mixin_client_features_parser(parser):
    """Add the arguments for the client to the parser

    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='Client Features')

    parser.add_argument(
        '--asyncio',
        action='store_true',
        default=False,
        help='If set, then the input and output of this Client work in an asynchronous manner. ',
    )

    gp.add_argument(
        '--request-size',
        type=int,
        default=100,
        help='The number of Documents in each Request.',
    )

    gp.add_argument(
        '--continue-on-error',
        action='store_true',
        default=False,
        help='If set, a Request that causes error will be logged only without blocking the further '
        'requests.',
    )

    gp.add_argument(
        '--show-progress',
        action='store_true',
        default=False,
        help='If set, client will show a progress bar on receiving every request.',
    )

    gp.add_argument(
        '--return-results',
        action='store_true',
        default=False,
        help='If set, the results of all Requests will be returned as a list. '
        'This is useful when one wants process Responses in bulk instead of using callback.',
    )
