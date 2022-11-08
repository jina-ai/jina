from jina.parsers.helper import add_arg_group


def mixin_head_parser(parser):
    """Mixing in arguments required by head pods and runtimes into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='Head')

    gp.add_argument(
        '--compression',
        choices=['NoCompression', 'Deflate', 'Gzip'],
        help='The compression mechanism used when sending requests from the Head to the WorkerRuntimes. For more details, '
        'check https://grpc.github.io/grpc/python/grpc.html#compression.',
    )

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

    gp.add_argument(
        '--timeout-send',
        type=int,
        default=None,
        help='The timeout in milliseconds used when sending data requests to Executors, -1 means no timeout, disabled by default',
    )
