__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import os


_SHOW_ALL_ARGS = 'JINA_FULL_CLI' in os.environ


def add_arg_group(parser, title):
    return parser.add_argument_group(title)


class KVAppendAction(argparse.Action):
    """
    argparse action to split an argument into KEY=VALUE form
    on the first = and append to a dictionary.
    This is used for setting up --env
    """

    def __call__(self, parser, args, values, option_string=None):
        import json
        d = getattr(args, self.dest) or {}
        for value in values:
            try:
                d.update(json.loads(value))
            except json.JSONDecodeError:
                try:
                    (k, v) = value.split('=', 2)
                except ValueError:
                    raise argparse.ArgumentError(f'could not parse argument \"{values[0]}\" as k=v format')
                d[k] = v
        setattr(args, self.dest, d)


def set_base_parser():
    from . import __version__
    from .helper import colored, get_full_version, format_full_version_info
    # create the top-level parser
    urls = {
        'Jina 101': ('🐣', 'https://101.jina.ai'),
        'Docs': ('📚', 'https://docs.jina.ai'),
        'Examples': ('🚀‍', 'https://learn.jina.ai'),
        'Dashboard': ('📊', 'https://dashboard.jina.ai'),
        'Code': ('🧑‍💻', 'https://opensource.jina.ai'),
        'Hiring!': ('🙌', 'career@jina.ai')
    }
    url_str = '\n'.join(f'{v[0]} {k:10.10}\t{colored(v[1], "cyan", attrs=["underline"])}' for k, v in urls.items())

    parser = argparse.ArgumentParser(
        epilog=f'Jina (v{colored(__version__, "green")}) is the cloud-native neural search solution '
               'powered by AI and deep learning technology.\n'
               'It provides a universal solution for large-scale index and query '
               'of media contents.\n'
               f'{url_str}',
        formatter_class=_chf,
        description='Jina Command Line Interface'
    )
    parser.add_argument('-v', '--version', action='version', version=__version__,
                        help='show Jina version')

    parser.add_argument('-vf', '--version-full', action='version',
                        version=format_full_version_info(*get_full_version()),
                        help='show Jina and all dependencies versions')
    return parser


def set_logger_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--groupby-regex', type=str,
                        default=r'(.*@\d+)\[',
                        help='the regular expression for grouping logs')
    parser.add_argument('--refresh-time', type=int,
                        default=5,
                        help='refresh time interval in seconds, set to -1 to persist all grouped logs')
    return parser


def set_hub_base_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--username', type=str, help='the Docker registry username',
                        default=os.environ.get('JINAHUB_USERNAME', ''))
    # _gp = parser.add_mutually_exclusive_group()
    # _gp.add_argument('--password-stdin', type=argparse.FileType('r'),
    #                  default=(sys.stdin if sys.stdin.isatty() else None),
    #                  help='take the password from stdin')
    parser.add_argument('--password', type=str, help='the plaintext password',
                        default=os.environ.get('JINAHUB_PASSWORD', ''))
    parser.add_argument('--registry', type=str, default='https://index.docker.io/v1/',
                        help='the URL to the Docker registry, e.g. https://index.docker.io/v1/')
    parser.add_argument('--repository', type=str, default='jinahub',
                        help='the Docker repository name, change this when pushing image to a personal repository')
    return parser


def set_hub_new_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--output-dir', type=str, default='.',
                        help='where to output the generated project dir into.')
    parser.add_argument('--template', type=str, default='https://github.com/jina-ai/cookiecutter-jina-hub.git',
                        help='cookiecutter template directory containing a project template directory, or a URL to a git repository. Only used when "--type template"')
    parser.add_argument('--type', type=str, default='pod', choices=['pod', 'app', 'template'],
                        help='create a template for executor hub pod or app using cookiecutter.')
    parser.add_argument('--overwrite', action='store_true', default=False,
                        help='overwrite the contents of output directory if it exists')
    return parser


def set_hub_build_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    set_hub_base_parser(parser)
    from .enums import BuildTestLevel

    parser.add_argument('path', type=str, help='path to the directory containing '
                                               'Dockerfile, manifest.yml, README.md '
                                               'zero or more yaml config, '
                                               'zero or more Python file. '
                                               'All files in this directory will be shipped into a Docker image')
    parser.add_argument('--pull', action='store_true', default=False,
                        help='downloads any updates to the FROM image in Dockerfiles')
    parser.add_argument('--push', action='store_true', default=False,
                        help='push the built image to the registry')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='only check path and validility, no real building')
    parser.add_argument('--prune-images', action='store_true', default=False,
                        help='prune unused images after building, this often saves disk space')
    parser.add_argument('--raise-error', action='store_true', default=False,
                        help='raise any error and exit with code 1')
    parser.add_argument('--test-uses', action='store_true', default=False,
                        help='after the build, test the image in "uses" with different level')
    parser.add_argument('--test-level', type=BuildTestLevel.from_string,
                        choices=list(BuildTestLevel), default=BuildTestLevel.FLOW,
                        help='the test level when "test-uses" is set, "NONE" means no test')
    parser.add_argument('--host-info', action='store_true', default=False,
                        help='store the host information during bookkeeping')
    parser.add_argument('--daemon', action='store_true', default=False,
                        help='run the test Pea/Pod as a daemon process, see "jina pea --help" for details')
    parser.add_argument('--no-overwrite', action='store_true', default=False,
                        help='Do not allow overwriting existing images (based on module version and jina version)')
    return parser


def set_hub_pushpull_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    set_hub_base_parser(parser)

    parser.add_argument('name', type=str, help='the name of the image.')
    return parser


def set_hub_list_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--name', type=str,
                        help='name of hub image')
    parser.add_argument('--kind', type=str,
                        help='kind of hub image')
    parser.add_argument('--keywords', type=str, nargs='+', metavar='KEYWORD',
                        help='keywords for searching')
    parser.add_argument('--type', type=str, default='pod', choices=['pod', 'app'],
                        help='type of the hub image')
    parser.add_argument('--local-only', action='store_true', default=False,
                        help='list all local hub images on the current machine')
    return parser


def set_hw_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from .helper import get_random_identity
    from pkg_resources import resource_filename

    gp = add_arg_group(parser, 'general arguments')
    gp.add_argument('--workdir', type=str, default=get_random_identity(),
                    help='the workdir for hello-world demo, '
                         'all data, indices, shards and outputs will be saved there')
    gp.add_argument('--logserver', action='store_true', default=False,
                    help='start a log server for the dashboard')
    gp.add_argument('--logserver-config', type=str,
                    default=resource_filename('jina',
                                              '/'.join(('resources', 'logserver.default.yml'))),
                    help='the yaml config of the log server')
    gp.add_argument('--download-proxy', type=str,
                    help='specify the proxy when downloading sample data')
    gp = add_arg_group(parser, 'scalability arguments')
    gp.add_argument('--shards', type=int,
                    default=2,
                    help='number of shards when index and query')
    gp.add_argument('--parallel', type=int,
                    default=2,
                    help='number of parallel when index and query')
    gp = add_arg_group(parser, 'index arguments')
    gp.add_argument('--uses-index', type=str,
                    default=resource_filename('jina', '/'.join(('resources', 'helloworld.flow.index.yml'))),
                    help='the yaml path of the index flow')
    gp.add_argument('--index-data-url', type=str,
                    default='http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-images-idx3-ubyte.gz',
                    help='the url of index data (should be in idx3-ubyte.gz format)')
    gp.add_argument('--index-batch-size', type=int,
                    default=1024,
                    help='the batch size in indexing')
    gp = add_arg_group(parser, 'query arguments')
    gp.add_argument('--uses-query', type=str,
                    default=resource_filename('jina', '/'.join(('resources', 'helloworld.flow.query.yml'))),
                    help='the yaml path of the query flow')
    gp.add_argument('--query-data-url', type=str,
                    default='http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-images-idx3-ubyte.gz',
                    help='the url of query data (should be in idx3-ubyte.gz format)')
    gp.add_argument('--query-batch-size', type=int,
                    default=32,
                    help='the batch size in searching')
    gp.add_argument('--num-query', type=int, default=128,
                    help='number of queries to visualize')
    gp.add_argument('--top-k', type=int, default=50,
                    help='top-k results to retrieve and visualize')

    return parser


def set_flow_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from .enums import FlowOutputType, FlowOptimizeLevel, FlowInspectType
    from .helper import get_random_identity

    gp = add_arg_group(parser, 'flow arguments')
    gp.add_argument('--uses', type=str, help='a yaml file represents a flow')
    from pkg_resources import resource_filename
    gp.add_argument('--logserver', action='store_true', default=False,
                    help='start a log server for the dashboard')
    gp.add_argument('--logserver-config', type=str,
                    default=resource_filename('jina',
                                              '/'.join(('resources', 'logserver.default.yml'))),
                    help='the yaml config of the log server')
    gp.add_argument('--log-id', type=str, default=get_random_identity(),
                    help='the log id used to aggregate logs by fluentd' if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp.add_argument('--optimize-level', type=FlowOptimizeLevel.from_string, default=FlowOptimizeLevel.NONE,
                    help='removing redundant routers from the flow. Note, this may change the gateway zmq socket to BIND \
                            and hence not allow multiple clients connected to the gateway at the same time.'
                    if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp.add_argument('--output-type', type=FlowOutputType.from_string,
                    choices=list(FlowOutputType), default=FlowOutputType.SHELL_PROC,
                    help='type of the output')
    gp.add_argument('--output-path', type=argparse.FileType('w', encoding='utf8'),
                    help='output path of the flow')
    gp.add_argument('--inspect', type=FlowInspectType.from_string,
                    choices=list(FlowInspectType), default=FlowInspectType.COLLECT,
                    help='strategy on those inspect pods in the flow. '
                         'if REMOVE is given then all inspect pods are removed when building the flow')
    return parser


def set_pea_parser(parser=None):
    from .enums import SocketType, PeaRoleType, SkipOnErrorType
    from .helper import random_port, get_random_identity
    from . import __default_host__

    if not parser:
        parser = set_base_parser()
    gp0 = add_arg_group(parser, 'pea basic arguments')
    gp0.add_argument('--name', type=str,
                     help='the name of this pea, used to identify the pod and its logs.')
    gp0.add_argument('--identity', type=str, default=get_random_identity(),
                     help='the identity of the sockets, default a random string (Important for load balancing messages'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp0.add_argument('--uses', type=str, default='_pass',
                     help='the config of the executor, it could be '
                          '> a YAML file path, '
                          '> a supported executor\'s class name, '
                          '> one of "_clear", "_pass", "_logforward" '
                          '> the content of YAML config (must starts with "!")'
                          '> a docker image')  # pod(no use) -> pea
    gp0.add_argument('--py-modules', type=str, nargs='*', metavar='PATH',
                     help='the customized python modules need to be imported before loading the'
                          ' executor')
    gp0.add_argument('--env', action=KVAppendAction,
                     metavar='KEY=VALUE', nargs='*',
                     help='a map of environment variables that are available to all peas in the pod.')

    gp1 = add_arg_group(parser, 'pea container arguments')
    gp1.add_argument('--uses-internal', type=str, default='BaseExecutor',
                     help='The executor config that is passed to the docker image if a docker image is used in uses. '
                          'It cannot be another docker image ')
    gp1.add_argument('--entrypoint', type=str,
                     help='the entrypoint command overrides the ENTRYPOINT in docker image. '
                          'when not set then the docker image ENTRYPOINT takes effective.')
    gp1.add_argument('--pull-latest', action='store_true', default=False,
                     help='pull the latest image before running')
    gp1.add_argument('--volumes', type=str, nargs='*', metavar='DIR',
                     help='the path on the host to be mounted inside the container. '
                          'they will be mounted to the root path, i.e. /user/test/my-workspace will be mounted to '
                          '/my-workspace inside the container. all volumes are mounted with read-write mode.')

    gp2 = add_arg_group(parser, 'pea network arguments')
    gp2.add_argument('--port-in', type=int, default=random_port(),
                     help='port for input data, default a random port between [49152, 65535]')
    gp2.add_argument('--port-out', type=int, default=random_port(),
                     help='port for output data, default a random port between [49152, 65535]')
    gp2.add_argument('--host-in', type=str, default=__default_host__,
                     help=f'host address for input, by default it is {__default_host__}')
    gp2.add_argument('--host-out', type=str, default=__default_host__,
                     help=f'host address for output, by default it is {__default_host__}')
    gp2.add_argument('--socket-in', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PULL_BIND,
                     help='socket type for input port')
    gp2.add_argument('--socket-out', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PUSH_BIND,
                     help='socket type for output port')
    gp2.add_argument('--port-ctrl', type=int, default=os.environ.get('JINA_CONTROL_PORT', random_port()),
                     help='port for controlling the pod, default a random port between [49152, 65535]')
    gp2.add_argument('--ctrl-with-ipc', action='store_true', default=False,
                     help='use ipc protocol for control socket')
    gp2.add_argument('--timeout', type=int, default=-1,
                     help='timeout (ms) of all requests, -1 for waiting forever')
    gp2.add_argument('--timeout-ctrl', type=int, default=5000,
                     help='timeout (ms) of the control request, -1 for waiting forever')
    gp2.add_argument('--timeout-ready', type=int, default=10000,
                     help='timeout (ms) of a pea is ready for request, -1 for waiting forever')
    gp2.add_argument('--expose-public', action='store_true', default=False,
                     help='expose the public IP address to remote when necessary, by default it exposes'
                          'private IP address, which only allows accessing under the same network/subnet')

    gp3 = add_arg_group(parser, 'pea IO arguments')
    gp3.add_argument('--dump-interval', type=int, default=240,
                     help='serialize the model in the pod every n seconds if model changes. '
                          '-1 means --read-only. ')
    gp3.add_argument('--read-only', action='store_true', default=False,
                     help='do not allow the pod to modify the model, '
                          'dump_interval will be ignored')
    gp3.add_argument('--separated-workspace', action='store_true', default=False,
                     help='the data and config files are separated for each pea in this pod, '
                          'only effective when BasePod\'s `parallel` > 1')
    gp3.add_argument('--pea-id', type=int, default=-1,
                     help='the id of the storage of this pea, only effective when `separated_workspace=True`'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp5 = add_arg_group(parser, 'pea messaging arguments')
    gp5.add_argument('--num-part', type=int, default=0,
                     help='the number of messages expected from upstream, 0 and 1 means single part'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp5.add_argument('--role', type=PeaRoleType.from_string, choices=list(PeaRoleType),
                     help='the role of this pea in a pod' if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp5.add_argument('--skip-on-error', type=SkipOnErrorType.from_string, choices=list(SkipOnErrorType),
                     default=SkipOnErrorType.NONE,
                     help='skip strategy on error message.')

    gp6 = add_arg_group(parser, 'pea EXPERIMENTAL arguments')
    gp6.add_argument('--memory-hwm', type=int, default=-1,
                     help='memory high watermark of this pod in Gigabytes, pod will restart when this is reached. '
                          '-1 means no restriction')
    gp6.add_argument('--runtime', type=str, choices=['thread', 'process'], default='process',
                     help='the parallel runtime of the pod')
    gp6.add_argument('--max-idle-time', type=int, default=60,
                     help='label this pea as inactive when it does not '
                          'process any request after certain time (in second)')
    gp6.add_argument('--daemon', action='store_true', default=False,
                     help='when a process exits, it attempts to terminate all of its daemonic child processes. '
                          'setting it to true basically tell the context manager do not wait on this Pea')

    from pkg_resources import resource_filename
    gp7 = add_arg_group(parser, 'logging arguments')
    gp7.add_argument('--log-config', type=str,
                     default=resource_filename('jina',
                                               '/'.join(('resources', 'logging.default.yml'))),
                     help='the yaml config of the logger. note the executor inside will inherit this log config')
    gp7.add_argument('--log-remote', action='store_true', default=False,
                     help='turn on remote logging, this should not be set manually'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp7.add_argument('--log-id', type=str, default=get_random_identity(),
                     help='the log id used to aggregate logs by fluentd' if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp8 = add_arg_group(parser, 'ssh tunneling arguments')
    gp8.add_argument('--ssh-server', type=str, default=None,
                     help='the SSH server through which the tunnel will be created, '
                          'can actually be a fully specified "user@server:port" ssh url.')
    gp8.add_argument('--ssh-keyfile', type=str, default=None,
                     help='this specifies a key to be used in ssh login, default None. '
                          'regular default ssh keys will be used without specifying this argument.')
    gp8.add_argument('--ssh-password', type=str, default=None,
                     help='ssh password to the ssh server.')
    _set_grpc_parser(parser)
    return parser


def set_pod_parser(parser=None):
    from .enums import PollingType, SchedulerType
    if not parser:
        parser = set_base_parser()
    set_pea_parser(parser)

    gp4 = add_arg_group(parser, 'pod replica arguments')
    gp4.add_argument('--parallel', '--shards', type=int, default=1,
                     help='number of parallel peas in the pod running at the same time, '
                          '`port_in` and `port_out` will be set to random, '
                          'and routers will be added automatically when necessary')
    gp4.add_argument('--polling', type=PollingType.from_string, choices=list(PollingType),
                     default=PollingType.ANY,
                     help='ANY: only one (whoever is idle) replica polls the message; '
                          'ALL: all workers poll the message (like a broadcast)')
    gp4.add_argument('--scheduling', type=SchedulerType.from_string, choices=list(SchedulerType),
                     default=SchedulerType.LOAD_BALANCE,
                     help='the strategy of scheduling workload among peas')
    gp4.add_argument('--uses-before', type=str,
                     help='the executor used before sending to all parallels, '
                          'accepted type follows "--uses"')
    gp4.add_argument('--uses-after', type=str,
                     help='the executor used after receiving from all parallels, '
                          'accepted type follows "--uses"')
    gp4.add_argument('--shutdown-idle', action='store_true', default=False,
                     help='shutdown this pod when all peas are idle')
    return parser


def set_ping_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('host', type=str,
                        help='host address of the target pod/pea, e.g. 0.0.0.0')
    parser.add_argument('port', type=int,
                        help='the control port of the target pod/pea')
    parser.add_argument('--timeout', type=int, default=3000,
                        help='timeout (ms) of one check, -1 for waiting forever')
    parser.add_argument('--retries', type=int, default=3,
                        help='max number of tried health checks before exit 1')
    parser.add_argument('--print-response', action='store_true', default=False,
                        help='print the response when received')
    return parser


def set_check_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--summary-exec', type=str,
                        help='the markdown file path for all executors summary')
    parser.add_argument('--summary-driver', type=str,
                        help='the markdown file path for all drivers summary')
    return parser


def set_export_api_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--yaml-path', type=str, nargs='*', metavar='PATH',
                        help='the YAML file path for storing the exported API')
    parser.add_argument('--json-path', type=str, nargs='*', metavar='PATH',
                        help='the JSON file path for storing the exported API')
    return parser


def _set_grpc_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from .helper import random_port
    from . import __default_host__
    from .enums import RemoteAccessType
    gp1 = add_arg_group(parser, 'grpc and remote arguments')
    gp1.add_argument('--host', type=str, default=__default_host__,
                     help=f'host address of the pea/gateway, by default it is {__default_host__}.')
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


# def set_grpc_service_parser(parser=None):
#     if not parser:
#         parser = set_base_parser()
#     set_pod_parser(parser)
#     _set_grpc_parser(parser)
#
#     parser.add_argument('--pb2-path',
#                         type=str,
#                         required=True,
#                         help='the path of the python file protocol buffer compiler')
#     parser.add_argument('--pb2-grpc-path',
#                         type=str,
#                         required=True,
#                         help='the path of the python file generated by the gRPC Python protocol compiler plugin')
#     parser.add_argument('--stub-name',
#                         type=str,
#                         required=True,
#                         help='the name of the gRPC Stub')
#     parser.add_argument('--api-name',
#                         type=str,
#                         required=True,
#                         help='the api name for calling the stub')
#     return parser


def set_gateway_parser(parser=None):
    from .enums import SocketType, CompressAlgo
    if not parser:
        parser = set_base_parser()
    set_pea_parser(parser)

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


def set_client_cli_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    from .enums import RequestType, CallbackOnType

    _set_grpc_parser(parser)

    gp1 = add_arg_group(parser, 'client-specific arguments')

    gp1.add_argument('--batch-size', type=int, default=100,
                     help='the number of documents in each request')
    gp1.add_argument('--mode', choices=list(RequestType), type=RequestType.from_string,
                     # required=True,
                     help='the mode of the client and the server')
    gp1.add_argument('--top-k', type=int,
                     help='top_k results returned in the search mode')
    gp1.add_argument('--mime-type', type=str,
                     help='MIME type of the input, useful when input-type is set to BUFFER')
    gp1.add_argument('--callback-on', choices=list(CallbackOnType), type=CallbackOnType.from_string,
                     default=CallbackOnType.REQUEST,
                     help='which field the output function should work with')
    gp1.add_argument('--timeout-ready', type=int, default=10000,
                     help='timeout (ms) of a pea is ready for request, -1 for waiting forever')
    gp1.add_argument('--skip-dry-run', action='store_true', default=False,
                     help='skip dry run (connectivity test) before sending every request')
    gp1.add_argument('--continue-on-error', action='store_true', default=False,
                     help='if to continue on all requests when callback function throws an error')
    return parser


def get_main_parser():
    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(dest='cli',
                               description='use "%(prog)-8s [sub-command] --help" '
                                           'to get detailed information about each sub-command', required=True)

    set_hw_parser(sp.add_parser('hello-world', help='👋 Hello World! Hello Jina!',
                                description='Start the hello-world demo, a simple end2end image index and search demo '
                                            'without any extra dependencies.',
                                formatter_class=_chf))

    # cli
    set_pod_parser(sp.add_parser('pod', help='start a pod',
                                 description='Start a Jina pod',
                                 formatter_class=_chf))

    set_flow_parser(sp.add_parser('flow',
                                  description='Start a Jina flow that consists of multiple pods',
                                  help='start a flow from a YAML file', formatter_class=_chf))
    set_gateway_parser(sp.add_parser('gateway',
                                     description='Start a Jina gateway that receives client remote requests via gRPC',
                                     help='start a gateway', formatter_class=_chf))

    set_ping_parser(
        sp.add_parser('ping', help='ping a pod and check the network connectivity',
                      description='Ping a remote pod and check the network connectivity',
                      formatter_class=_chf))
    set_check_parser(
        sp.add_parser('check', help='check the import status all executors and drivers',
                      description='Check the import status all executors and drivers',
                      formatter_class=_chf))

    pp = sp.add_parser('hub', help='build, push, pull Jina Hub images',
                       description='Build, push, pull Jina Hub images',
                       formatter_class=_chf)

    spp = pp.add_subparsers(dest='hub',
                            description='use "%(prog)-8s [sub-command] --help" '
                                        'to get detailed information about each sub-command', required=True)

    spp.add_parser('login', help='login via Github to push images to Jina hub registry',
                   description='Login via Github to push images to Jina hub registry',
                   formatter_class=_chf)

    set_hub_new_parser(
        spp.add_parser('new', aliases=['init', 'create'], help='create a new Hub executor or app using cookiecutter',
                       description='Create a new Hub executor or app using cookiecutter',
                       formatter_class=_chf))

    set_hub_build_parser(
        spp.add_parser('build', help='build a directory into Jina hub image',
                       description='Build a directory into Jina hub image',
                       formatter_class=_chf))

    set_hub_pushpull_parser(
        spp.add_parser('push', help='push an image to the Jina hub registry',
                       description='Push an image to the Jina hub registry',
                       formatter_class=_chf))

    set_hub_pushpull_parser(
        spp.add_parser('pull', help='pull an image from the Jina hub registry to local',
                       description='Pull an image to the Jina hub registry to local',
                       formatter_class=_chf))

    set_hub_list_parser(
        spp.add_parser('list', help='list hub executors from jina hub registry',
                       description='List hub executors from jina hub registry',
                       formatter_class=_chf))

    set_pea_parser(sp.add_parser('pea',
                                 description='Start a Jina pea. '
                                             'You should rarely use this directly unless you '
                                             'are doing low-level orchestration',
                                 formatter_class=_chf, **(dict(help='start a pea')) if _SHOW_ALL_ARGS else {}))

    set_logger_parser(sp.add_parser('log',
                                    description='Receive piped log output and beautify the log. '
                                                'Depreciated, use Jina Dashboard instead',
                                    formatter_class=_chf,
                                    **(dict(help='beautify the log')) if _SHOW_ALL_ARGS else {}))
    set_client_cli_parser(
        sp.add_parser('client',
                      description='Start a Python client that connects to a remote Jina gateway',
                      formatter_class=_chf, **(dict(help='start a client')) if _SHOW_ALL_ARGS else {}))

    set_export_api_parser(sp.add_parser('export-api',
                                        description='Export Jina API to JSON/YAML file for 3rd party applications',
                                        formatter_class=_chf,
                                        **(dict(help='export Jina API to file')) if _SHOW_ALL_ARGS else {}))
    return parser


class _ColoredHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    class _Section(object):

        def __init__(self, formatter, parent, heading=None):
            self.formatter = formatter
            self.parent = parent
            self.heading = heading
            self.items = []

        def format_help(self):
            # format the indented section
            if self.parent is not None:
                self.formatter._indent()
            join = self.formatter._join_parts
            item_help = join([func(*args) for func, args in self.items])
            if self.parent is not None:
                self.formatter._dedent()

            # return nothing if the section was empty
            if not item_help:
                return ''

            # add the heading if the section was non-empty
            if self.heading is not argparse.SUPPRESS and self.heading is not None:
                from .helper import colored
                current_indent = self.formatter._current_indent
                captial_heading = ' '.join(v[0].upper() + v[1:] for v in self.heading.split(' '))
                heading = '⚙️  %*s%s\n' % (
                    current_indent, '', colored(captial_heading, 'cyan', attrs=['underline', 'bold', 'reverse']))
            else:
                heading = ''

            # join the section-initial newline, the heading and the help
            return join(['\n', heading, item_help, '\n'])

    def start_section(self, heading):
        self._indent()
        section = self._Section(self, self._current_section, heading)
        self._add_item(section.format_help, [])
        self._current_section = section

    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                from .helper import colored
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if isinstance(action, argparse._StoreTrueAction):

                    help += colored(' (default: %s)' % (
                        'enabled' if action.default else f'disabled, use "--{action.dest}" to enable it'),
                                    attrs=['dark'])
                elif action.choices:
                    choices_str = f'{{{", ".join([str(c) for c in action.choices])}}}'
                    help += colored(' (choose from: ' + choices_str + '; default: %(default)s)', attrs=['dark'])
                elif action.option_strings or action.nargs in defaulting_nargs:
                    help += colored(' (type: %(type)s; default: %(default)s)', attrs=['dark'])
        return help

    def _get_default_metavar_for_optional(self, action):
        return ''

    # def _get_default_metavar_for_positional(self, action):
    #     return ''

    def _expand_help(self, action):
        params = dict(vars(action), prog=self._prog)
        for name in list(params):
            if params[name] is argparse.SUPPRESS:
                del params[name]
        for name in list(params):
            if hasattr(params[name], '__name__'):
                params[name] = params[name].__name__
        return self._get_help_string(action) % params

    def _metavar_formatter(self, action, default_metavar):
        if action.metavar is not None:
            result = action.metavar
        elif action.choices is not None:

            if len(action.choices) > 4:
                choice_strs = ', '.join([str(c) for c in action.choices][:4])
                result = f'{{{choice_strs} ... {len(action.choices) - 4} more choices}}'
            else:
                choice_strs = ', '.join([str(c) for c in action.choices])
                result = f'{{{choice_strs}}}'
        else:
            result = default_metavar

        def format(tuple_size):
            if isinstance(result, tuple):
                return result
            else:
                return (result,) * tuple_size

        return format

    def _fill_text(self, text, width, indent):
        return ''.join(indent + line for line in text.splitlines(keepends=True))


_chf = _ColoredHelpFormatter
