"""Argparser module for remote runtime"""
from ...helper import add_arg_group
from .... import __default_host__
from ....enums import CompressAlgo
from ....helper import random_port


def mixin_remote_parser(parser):
    """Add the options for remote expose
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Expose')

    gp.add_argument('--host', type=str, default=__default_host__,
                    help=f'The host address of the runtime, by default it is {__default_host__}.')

    gp.add_argument('--port-expose',
                    type=int,
                    default=random_port(),
                    help='The port of the host exposed to the public')


def mixin_grpc_parser(parser=None):
    """Add the options for gRPC
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='GRPC/REST')

    gp.add_argument('--max-message-size', type=int, default=-1,
                    help='The maximum send and receive size for gRPC server in bytes, -1 means unlimited')
    gp.add_argument('--proxy', action='store_true', default=False,
                    help='If set, respect the http_proxy and https_proxy environment variables. '
                         'otherwise, it will unset these proxy variables before start. '
                         'gRPC seems to prefer no proxy')
    gp.add_argument('--prefetch', type=int, default=50,
                    help='The number of pre-fetched requests from the client')
    gp.add_argument('--prefetch-on-recv', type=int, default=1,
                    help='The number of additional requests to fetch on every receive')
    gp.add_argument('--restful', '--rest-api', action='store_true', default=False,
                    help='If set, use RESTful interface instead of gRPC as the main interface')
    gp.add_argument('--compress', type=CompressAlgo.from_string, choices=list(CompressAlgo), default=CompressAlgo.LZ4,
                    help='''
The compress algorithm used over the entire Flow. 

Note that this is not necessarily effective, it depends on the settings of `--compress-lwm` and `compress-hwm`''')
    gp.add_argument('--compress-min-bytes', type=int, default=1024,
                    help='The original message size must be larger than this number to trigger the compress algorithm, '
                         '-1 means disable compression.')
    gp.add_argument('--compress-min-ratio', type=float, default=1.1,
                    help='The compression ratio (uncompressed_size/compressed_size) must be higher than this number '
                         'to trigger the compress algorithm.')
