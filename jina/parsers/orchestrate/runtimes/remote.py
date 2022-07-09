"""Argparser module for remote runtime"""

from jina import __default_host__, helper
from jina.parsers.helper import KVAppendAction, add_arg_group


def mixin_remote_runtime_parser(parser):
    """Add the options for a remote Executor
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='RemoteRuntime')
    _add_host(gp)


def mixin_client_gateway_parser(parser):
    """Add the options for the client connecting to the Gateway
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='ClientGateway')
    _add_host(gp)
    _add_proxy(gp)

    gp.add_argument(
        '--port',
        type=int,
        default=None,
        help='The port of the Gateway, which the client should connect to.',
    )

    gp.add_argument(
        '--tls',
        action='store_true',
        default=False,
        help='If set, connect to gateway using tls encryption',
    )


def mixin_gateway_parser(parser):
    """Add the options for remote expose at the Gateway
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Gateway')
    _add_host(gp)
    _add_proxy(gp)

    gp.add_argument(
        '--port-expose',
        type=int,
        dest='port',
        default=helper.random_port(),
        help='The port that the gateway exposes for clients for GRPC connections.',
    )

    parser.add_argument(
        '--graph-description',
        type=str,
        help='Routing graph for the gateway',
        default='{}',
    )

    parser.add_argument(
        '--graph-conditions',
        type=str,
        help='Dictionary stating which filtering conditions each Executor in the graph requires to receive Documents.',
        default='{}',
    )

    parser.add_argument(
        '--deployments-addresses',
        type=str,
        help='dictionary JSON with the input addresses of each Deployment',
        default='{}',
    )

    parser.add_argument(
        '--deployments-disable-reduce',
        type=str,
        help='list JSON disabling the built-in merging mechanism for each Deployment listed',
        default='[]',
    )

    gp.add_argument(
        '--compression',
        choices=['NoCompression', 'Deflate', 'Gzip'],
        help='The compression mechanism used when sending requests from the Head to the WorkerRuntimes. For more details, '
        'check https://grpc.github.io/grpc/python/grpc.html#compression.',
    )

    gp.add_argument(
        '--timeout-send',
        type=int,
        default=None,
        help='The timeout in milliseconds used when sending data requests to Executors, -1 means no timeout, disabled by default',
    )


def _add_host(arg_group):
    arg_group.add_argument(
        '--host',
        type=str,
        default=__default_host__,
        help=f'The host address of the runtime, by default it is {__default_host__}.',
    )


def _add_proxy(arg_group):

    arg_group.add_argument(
        '--proxy',
        action='store_true',
        default=False,
        help='If set, respect the http_proxy and https_proxy environment variables. '
        'otherwise, it will unset these proxy variables before start. '
        'gRPC seems to prefer no proxy',
    )


def mixin_graphql_parser(parser=None):
    """Add the options to rest server

    :param parser: the parser
    """

    gp = add_arg_group(parser, title='GraphQL')
    gp.add_argument(
        '--expose-graphql-endpoint',
        action='store_true',
        default=False,
        help='If set, /graphql endpoint is added to HTTP interface. ',
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
        '--no-debug-endpoints',
        action='store_true',
        default=False,
        help='If set, `/status` `/post` endpoints are removed from HTTP interface. ',
    )

    gp.add_argument(
        '--no-crud-endpoints',
        action='store_true',
        default=False,
        help='''
        If set, `/index`, `/search`, `/update`, `/delete` endpoints are removed from HTTP interface.

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

    gp.add_argument(
        '--uvicorn-kwargs',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server

More details can be found in Uvicorn docs: https://www.uvicorn.org/settings/

''',
    )

    gp.add_argument(
        '--grpc-server-kwargs',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
    Dictionary of kwargs arguments that will be passed to the grpc server when starting the server # todo update
    ''',
    )

    gp.add_argument(
        '--ssl-certfile',
        type=str,
        help='''
        the path to the certificate file
        ''',
        dest='ssl_certfile',
    )

    gp.add_argument(
        '--ssl-keyfile',
        type=str,
        help='''
        the path to the key file
        ''',
        dest='ssl_keyfile',
    )


def mixin_prefetch_parser(parser=None):
    """Add the options for prefetching
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Prefetch')

    gp.add_argument(
        '--prefetch',
        type=int,
        default=1000,
        help='''
    Number of requests fetched from the client before feeding into the first Executor. 
    
    Used to control the speed of data input into a Flow. 0 disables prefetch (1000 requests is the default)''',
    )
