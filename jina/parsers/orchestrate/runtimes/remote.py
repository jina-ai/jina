"""Argparser module for remote runtime"""
from jina import __default_host__, helper
from jina.enums import CompressAlgo
from jina.parsers.helper import KVAppendAction, add_arg_group


def mixin_remote_runtime_parser(parser):
    """Add the options for a remote Executor
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='RemoteRuntime')
    _add_host(gp)

    gp.add_argument(
        '--port-jinad',
        type=int,
        default=8000,
        help='The port of the remote machine for usage with JinaD.',
    )


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
        default=helper.random_port(),
        help='The port of the Gateway, which the client should connect to.',
    )

    gp.add_argument(
        '--https',
        action='store_true',
        default=False,
        help='If set, connect to gateway using https',
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
        '--deployments-addresses',
        type=str,
        help='dictionary JSON with the input addresses of each Deployment',
        default='{}',
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


def mixin_prefetch_parser(parser=None):
    """Add the options for prefetching
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Prefetch')

    gp.add_argument(
        '--prefetch',
        type=int,
        default=0,
        help='''
    Number of requests fetched from the client before feeding into the first Executor. 
    
    Used to control the speed of data input into a Flow. 0 disables prefetch (disabled by default)''',
    )
