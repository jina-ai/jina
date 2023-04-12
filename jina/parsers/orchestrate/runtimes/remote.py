"""Argparser module for remote runtime"""

from jina.constants import __default_host__
from jina.parsers.helper import CastHostAction, KVAppendAction, add_arg_group
from jina.parsers.orchestrate.runtimes.grpc_channel import (
    mixin_grpc_channel_options_parser,
)
from jina.parsers.orchestrate.runtimes.runtime import mixin_base_runtime_parser


def mixin_remote_runtime_parser(parser):
    """Add the options for a remote Executor
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='RemoteRuntime')

    gp.add_argument(
        '--host',
        '--host-in',
        nargs='+',
        default=[__default_host__],
        action=CastHostAction,
        help=f'The host of the Gateway, which the client should connect to, by default it is {__default_host__}.'
             ' In the case of an external Executor (`--external` or `external=True`) this can be a list of hosts. '
             ' Then, every resulting address will be considered as one replica of the Executor.',
    )


def mixin_client_gateway_parser(parser):
    """Add the options for the client connecting to the Gateway
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='ClientGateway')
    _add_proxy(gp)

    gp.add_argument(
        '--host',
        '--host-in',
        type=str,
        default=__default_host__,
        help=f'The host of the Gateway, which the client should connect to, by default it is {__default_host__}.',
    )

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


def mixin_gateway_streamer_parser(arg_group):
    """Mixin for gateway stream arguments.
    :param arg_group: args group
    """
    arg_group.add_argument(
        '--graph-description',
        type=str,
        help='Routing graph for the gateway',
        default='{}',
    )

    arg_group.add_argument(
        '--graph-conditions',
        type=str,
        help='Dictionary stating which filtering conditions each Executor in the graph requires to receive Documents.',
        default='{}',
    )

    arg_group.add_argument(
        '--deployments-addresses',
        type=str,
        help='JSON dictionary with the input addresses of each Deployment',
        default='{}',
    )

    arg_group.add_argument(
        '--deployments-metadata',
        type=str,
        help='JSON dictionary with the request metadata for each Deployment',
        default='{}',
    )

    arg_group.add_argument(
        '--deployments-no-reduce',
        '--deployments-disable-reduce',
        type=str,
        help='list JSON disabling the built-in merging mechanism for each Deployment listed',
        default='[]',
    )

    arg_group.add_argument(
        '--compression',
        choices=['NoCompression', 'Deflate', 'Gzip'],
        help='The compression mechanism used when sending requests from the Head to the WorkerRuntimes. For more details, '
             'check https://grpc.github.io/grpc/python/grpc.html#compression.',
    )

    arg_group.add_argument(
        '--timeout-send',
        type=int,
        default=None,
        help='The timeout in milliseconds used when sending data requests to Executors, -1 means no timeout, disabled by default',
    )


def mixin_gateway_parser(parser):
    """Add the options for remote expose at the Gateway
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='Gateway')
    _add_host(gp)
    _add_proxy(gp)

    gp.add_argument(
        '--uses',
        type=str,
        default=None,
        # TODO: add Jina Hub Gateway
        help='''
        The config of the gateway, it could be one of the followings:
        * the string literal of an Gateway class name
        * a Gateway YAML file (.yml, .yaml, .jaml)
        * a docker image (must start with `docker://`)
        * the string literal of a YAML config (must start with `!` or `jtype: `)
        * the string literal of a JSON config

        When use it under Python, one can use the following values additionally:
        - a Python dict that represents the config
        - a text file stream has `.read()` interface
        ''',
    )

    gp.add_argument(
        '--uses-with',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
    Dictionary of keyword arguments that will override the `with` configuration in `uses`
    ''',
    )

    gp.add_argument(
        '--py-modules',
        type=str,
        nargs='*',
        metavar='PATH',
        help='''
The customized python modules need to be imported before loading the gateway

Note that the recommended way is to only import a single module - a simple python file, if your
gateway can be defined in a single file, or an ``__init__.py`` file if you have multiple files,
which should be structured as a python package.
''',
    )

    gp.add_argument(
        '--replicas',
        type=int,
        default=1,
        help='The number of replicas of the Gateway. This replicas will only be applied when converted into Kubernetes YAML',
    )

    mixin_base_runtime_parser(gp)
    mixin_grpc_channel_options_parser(gp)
    mixin_gateway_streamer_parser(gp)


def _add_host(arg_group):
    arg_group.add_argument(
        '--host',
        '--host-in',
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

    _mixin_http_server_parser(gp)

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

        Any executor that has `@requests(on=...)` bound with those values will receive data requests.
        ''',
    )

    gp.add_argument(
        '--expose-endpoints',
        type=str,
        help='''
        A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints.
        ''',
    )


def _mixin_http_server_parser(arg_group):
    arg_group.add_argument(
        '--title',
        type=str,
        help='The title of this HTTP server. It will be used in automatics docs such as Swagger UI.',
    )

    arg_group.add_argument(
        '--description',
        type=str,
        help='The description of this HTTP server. It will be used in automatics docs such as Swagger UI.',
    )

    arg_group.add_argument(
        '--cors',
        action='store_true',
        default=False,
        help='''
        If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
        ''',
    )
    arg_group.add_argument(
        '--uvicorn-kwargs',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server

More details can be found in Uvicorn docs: https://www.uvicorn.org/settings/

''',
    )
    arg_group.add_argument(
        '--ssl-certfile',
        type=str,
        help='''
        the path to the certificate file
        ''',
        dest='ssl_certfile',
    )

    arg_group.add_argument(
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
