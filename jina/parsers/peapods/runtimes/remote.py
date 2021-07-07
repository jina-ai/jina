"""Argparser module for remote runtime"""
from ...helper import add_arg_group
from .... import __default_host__
from .... import helper
from ....enums import CompressAlgo


def mixin_remote_parser(parser):
    """Add the options for remote expose
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Expose')

    gp.add_argument(
        '--host',
        type=str,
        default=__default_host__,
        help=f'The host address of the runtime, by default it is {__default_host__}.',
    )

    gp.add_argument(
        '--port-expose',
        type=int,
        default=helper.random_port(),
        help='The port of the host exposed to the public',
    )

    gp.add_argument(
        '--proxy',
        action='store_true',
        default=False,
        help='If set, respect the http_proxy and https_proxy environment variables. '
        'otherwise, it will unset these proxy variables before start. '
        'gRPC seems to prefer no proxy',
    )


def mixin_http_gateway_parser(parser=None):
    """Add the options to rest server

    :param parser: the parser
    """
    gp = add_arg_group(parser, title='HTTP Gateway')

    gp.add_argument(
        '--title',
        type=str,
        help='The title of this HTTP server. It will be used in automatics docs such as Swagger UI.',
    )

    gp.add_argument(
        '--description',
        type=str,
        help='The description of this HTTP server. It will be used in automatics docs such as Swagger UI.',
    )

    gp.add_argument(
        '--cors',
        action='store_true',
        default=False,
        help='''
        If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
        ''',
    )

    gp.add_argument(
        '--default-swagger-ui',
        action='store_true',
        default=False,
        help='If set, the default swagger ui is used for `/docs` endpoint. ',
    )

    gp.add_argument(
        '--no-debug-endpoints',
        action='store_true',
        default=False,
        help='If set, /status /post endpoints are removed from HTTP interface. ',
    )

    gp.add_argument(
        '--no-crud-endpoints',
        action='store_true',
        default=False,
        help='''
        If set, /index, /search, /update, /delete endpoints are removed from HTTP interface.

        Any executor that has `@requests(on=...)` bind with those values will receive data requests.
        ''',
    )

    gp.add_argument(
        '--expose-endpoints',
        type=str,
        help='''
        A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints.
        ''',
    )


def mixin_prefetch_parser(parser=None):
    """Add the options for prefetching
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Prefetch')

    gp.add_argument(
        '--prefetch',
        type=int,
        default=50,
        help='The number of pre-fetched requests from the client',
    )
    gp.add_argument(
        '--prefetch-on-recv',
        type=int,
        default=1,
        help='The number of additional requests to fetch on every receive',
    )


def mixin_compressor_parser(parser=None):
    """Add the options for compressors
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Compression')

    gp.add_argument(
        '--compress',
        type=CompressAlgo.from_string,
        choices=list(CompressAlgo),
        default=CompressAlgo.NONE,
        help='''
    The compress algorithm used over the entire Flow.

    Note that this is not necessarily effective,
    it depends on the settings of `--compress-min-bytes` and `compress-min-ratio`''',
    )

    gp.add_argument(
        '--compress-min-bytes',
        type=int,
        default=1024,
        help='The original message size must be larger than this number to trigger the compress algorithm, '
        '-1 means disable compression.',
    )

    gp.add_argument(
        '--compress-min-ratio',
        type=float,
        default=1.1,
        help='The compression ratio (uncompressed_size/compressed_size) must be higher than this number '
        'to trigger the compress algorithm.',
    )
