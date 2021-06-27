"""Module for argparse for Client"""


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

    parser.add_argument(
        '--asyncio',
        action='store_true',
        default=False,
        help='If set, then the input and output of this Client work in an asynchronous manner. ',
    )
