from ...base import set_base_parser
from ...helper import add_arg_group
from ....helper import random_port


def mixin_remote_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    gp1 = add_arg_group(parser, title='Expose')

    gp1.add_argument('--port-expose', '--port-grpc', '--port-rest',
                     type=int,
                     default=random_port(),
                     help='host port of the gateway, "port-grpc" alias will be removed in future versions')
    return parser


def mixin_grpc_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    gp1 = add_arg_group(parser, title='GRPC')

    gp1.add_argument('--max-message-size', type=int, default=-1,
                     help='maximum send and receive size for grpc server in bytes, -1 means unlimited')
    gp1.add_argument('--proxy', action='store_true', default=False,
                     help='respect the http_proxy and https_proxy environment variables. '
                          'otherwise, it will unset these proxy variables before start. '
                          'gRPC seems to prefer no proxy')
    gp1.add_argument('--prefetch', type=int, default=50,
                     help='the number of pre-fetched requests from the client')
    gp1.add_argument('--prefetch-on-recv', type=int, default=1,
                     help='the number of additional requests to fetch on every receive')
    return parser
