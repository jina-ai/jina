"""Module for argparse for Client"""


def mixin_comm_protocol_parser(parser):
    """Add the arguments for the protocol to the parser

    :param parser: the parser configure
    """

    from jina.enums import GatewayProtocolType

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

    parser.add_argument(
        '--tracing',
        action='store_true',
        default=False,
        help='If set, the sdk implementation of the OpenTelemetry tracer will be available and will be enabled for automatic tracing of requests and customer span creation. '
        'Otherwise a no-op implementation will be provided.',
    )

    parser.add_argument(
        '--traces-exporter-host',
        type=str,
        default=None,
        help='If tracing is enabled, this hostname will be used to configure the trace exporter agent.',
    )

    parser.add_argument(
        '--traces-exporter-port',
        type=int,
        default=None,
        help='If tracing is enabled, this port will be used to configure the trace exporter agent.',
    )

    parser.add_argument(
        '--metrics',
        action='store_true',
        default=False,
        help='If set, the sdk implementation of the OpenTelemetry metrics will be available for default monitoring and custom measurements. '
        'Otherwise a no-op implementation will be provided.',
    )

    parser.add_argument(
        '--metrics-exporter-host',
        type=str,
        default=None,
        help='If tracing is enabled, this hostname will be used to configure the metrics exporter agent.',
    )

    parser.add_argument(
        '--metrics-exporter-port',
        type=int,
        default=None,
        help='If tracing is enabled, this port will be used to configure the metrics exporter agent.',
    )
