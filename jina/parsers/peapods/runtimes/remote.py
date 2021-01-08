from ...helper import add_arg_group
from ....helper import random_port
from .... import __default_host__


def mixin_remote_parser(parser):
    gp = add_arg_group(parser, title='Expose')

    gp.add_argument('--host', type=str, default=__default_host__,
                    help=f'host address of the runtime, by default it is {__default_host__}.')

    gp.add_argument('--port-expose',
                    type=int,
                    default=random_port(),
                    help='host port exposed to the public')


def mixin_grpc_parser(parser=None):
    gp = add_arg_group(parser, title='GRPC/REST')

    gp.add_argument('--max-message-size', type=int, default=-1,
                    help='maximum send and receive size for gRPC server in bytes, -1 means unlimited')
    gp.add_argument('--proxy', action='store_true', default=False,
                    help='respect the http_proxy and https_proxy environment variables. '
                         'otherwise, it will unset these proxy variables before start. '
                         'gRPC seems to prefer no proxy')
    gp.add_argument('--prefetch', type=int, default=50,
                    help='the number of pre-fetched requests from the client')
    gp.add_argument('--prefetch-on-recv', type=int, default=1,
                    help='the number of additional requests to fetch on every receive')
    gp.add_argument('--restful', '--rest-api', action='store_true', default=False,
                    help='use RESTful interface instead of gRPC as the main interface')
