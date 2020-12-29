
def _set_grpc_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from .helper import random_port
    from . import __default_host__
    from .enums import RemoteAccessType
    gp1 = add_arg_group(parser, 'grpc and remote arguments')

    gp1.add_argument('--port-expose', '--port-grpc',
                     type=int,
                     default=random_port(),
                     help='host port of the gateway, "port-grpc" alias will be removed in future versions')
    gp1.add_argument('--max-message-size', type=int, default=-1,
                     help='maximum send and receive size for grpc server in bytes, -1 means unlimited')
    gp1.add_argument('--proxy', action='store_true', default=False,
                     help='respect the http_proxy and https_proxy environment variables. '
                          'otherwise, it will unset these proxy variables before start. '
                          'gRPC seems to prefer no proxy')
    gp1.add_argument('--remote-access', choices=list(RemoteAccessType),
                     default=RemoteAccessType.JINAD,
                     type=RemoteAccessType.from_string,
                     help=f'host address of the pea/gateway, by default it is {__default_host__}.')
    return parser


def set_gateway_parser(parser=None):
    from .enums import SocketType, CompressAlgo
    if not parser:
        parser = set_base_parser()
    set_pea_parser(parser)
    _set_grpc_parser(parser)

    gp1 = add_arg_group(parser, 'gateway arguments')
    gp1.set_defaults(name='gateway',
                     socket_in=SocketType.PULL_CONNECT,  # otherwise there can be only one client at a time
                     socket_out=SocketType.PUSH_CONNECT,
                     ctrl_with_ipc=True,  # otherwise ctrl port would be conflicted
                     read_only=True)
    gp1.add_argument('--prefetch', type=int, default=50,
                     help='the number of pre-fetched requests from the client')
    gp1.add_argument('--prefetch-on-recv', type=int, default=1,
                     help='the number of additional requests to fetch on every receive')
    gp1.add_argument('--rest-api', action='store_true', default=False,
                     help='use REST-API as the interface instead of gRPC with port number '
                          'set to the value of "port-expose"')

    gp2 = add_arg_group(parser, 'envelope attribute arguments')
    gp2.add_argument('--check-version', action='store_true', default=False,
                     help='comparing the jina and proto version of incoming message with local setup, '
                          'mismatch raise an exception')
    gp2.add_argument('--compress', choices=list(CompressAlgo), type=CompressAlgo.from_string,
                     default=CompressAlgo.LZ4,
                     help='the algorithm used for compressing request data, this can reduce the network overhead but may '
                          'increase CPU usage')
    gp2.add_argument('--compress-hwm', type=int, default=100,
                     help='the high watermark that triggers the message compression. '
                          'message bigger than this HWM (in bytes) will be compressed by lz4 algorithm.'
                          'set this to 0 to disable this feature.')
    gp2.add_argument('--compress-lwm', type=float, default=0.9,
                     help='the low watermark that enables the sending of a compressed message. '
                          'compression rate (after_size/before_size) lower than this LWM will be considered as successeful '
                          'compression, and will be sent. Otherwise, it will send the original message without compression')
    # gp1.add_argument('--to-datauri', action='store_true', default=False,
    #                  help='always represent the result document with data URI, instead of using buffer/blob/text')
    return parser
