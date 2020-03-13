import argparse

from ..helper import colored


def add_arg_group(parser, title):
    return parser.add_argument_group(' '.join(v[0].upper() + v[1:] for v in title.split(' ')))


def set_base_parser():
    from .. import __version__, __proto_version__
    from google.protobuf.internal import api_implementation
    from ..helper import colored
    import os, zmq, numpy, google.protobuf, grpc, ruamel.yaml
    from grpc import _grpcio_metadata
    # create the top-level parser
    parser = argparse.ArgumentParser(
        epilog='Jina (v%s) is a cloud-native semantic search engine '
               'powered by deep neural networks.\n'
               'It provides a universal solution of large-scale index and query '
               'for media contents.\nVisit %s for documentations.' % (
                   colored(__version__, 'green'),
                   colored('https://docs.jina.ai', 'cyan', attrs=['underline'])),
        formatter_class=_chf)

    parser.add_argument('-v', '--version', action='version',
                        version='jina: %s\n'
                                'jina-proto: %s\n'
                                'jina-vcs-tag: %s\n'
                                'libzmq: %s\n'
                                'pyzmq: %s\n'
                                'numpy: %s\n'
                                'protobuf: %s\n'
                                'proto-backend: %s\n'
                                'grpcio: %s\n'
                                'ruamel.yaml: %s\n'
                                %
                                (__version__,
                                 __proto_version__,
                                 os.environ.get('JINA_VCS_VERSION', colored('(unset)', 'yellow')),
                                 zmq.zmq_version(),
                                 zmq.__version__,
                                 numpy.__version__,
                                 google.protobuf.__version__,
                                 api_implementation._default_implementation_type,
                                 getattr(grpc, '__version__', _grpcio_metadata.__version__),
                                 ruamel.yaml.__version__),
                        help='show version and crucial dependants, environment variables')
    gp1 = add_arg_group(parser, 'logging arguments')
    gp1.add_argument('--sse', action='store_true', default=False,
                     help='turn on server-side event logging')
    gp1.add_argument('--profiling', action='store_true', default=False,
                     help='turn on the profiling logger')
    return parser


def set_logger_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--groupby_regex', type=str,
                        default=r'(.*@\d+)\[',
                        help='the regular expression for grouping logs')
    parser.add_argument('--refresh_time', type=int,
                        default=5,
                        help='refresh time interval in seconds, set to -1 to persist all grouped logs')
    return parser


def set_flow_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from ..enums import FlowOutputType

    gp = add_arg_group(parser, 'flow arguments')
    gp.add_argument('flow_yaml_path', type=str, help='a yaml file represents a flow')
    gp.add_argument('--output_type', type=FlowOutputType.from_string,
                    choices=list(FlowOutputType), default=FlowOutputType.SHELL_PROC,
                    help='type of the output')
    gp.add_argument('--output_path', type=argparse.FileType('w', encoding='utf8'),
                    help='output path of the flow')

    return parser


def set_pea_parser(parser=None):
    from ..enums import SocketType
    from ..helper import random_port, random_identity
    from .. import __default_host__
    import os
    if not parser:
        parser = set_base_parser()

    gp0 = add_arg_group(parser, 'pea basic arguments')
    gp0.add_argument('--name', type=str,
                     help='the name of this pod, used to identify the pod and its logs.')
    gp0.add_argument('--identity', type=str, default=random_identity(),
                     help='the identity of the pod, default a random string')
    gp0.add_argument('--yaml_path', type=str, default='BaseExecutor',
                     help='the yaml config of the executor, it should be a readable stream,'
                          ' or a valid file path, or a supported class name.')  # pod(no use) -> pea

    gp1 = add_arg_group(parser, 'pea container arguments')
    gp1.add_argument('--image', type=str,
                     help='the name of the docker image that this pea runs with. it is also served as an indicator '
                          'of containerization. '
                          'when this and --yaml_path are both given then the docker image '
                          'is used and its original yaml configuration is replaced by the given yaml_path')
    gp1.add_argument('--entrypoint', type=str,
                     help='the entrypoint command overrides the ENTRYPOINT in docker image. '
                          'when not set then the docker image ENTRYPOINT takes effective.')
    gp1.add_argument('--pull_latest', action='store_true', default=False,
                     help='pull the latest image before running')
    gp1.add_argument('--volumes', type=str, nargs='*',
                     help='the path on the host to be mounted inside the container. '
                          'they will be mounted to the root path, i.e. /user/test/my-workspace will be mounted to '
                          '/my-workspace inside the container. all volumes are mounted with read-write mode.')

    gp2 = add_arg_group(parser, 'pea network arguments')
    gp2.add_argument('--port_in', type=int, default=random_port(),
                     help='port for input data, default a random port between [49152, 65536]')
    gp2.add_argument('--port_out', type=int, default=random_port(),
                     help='port for output data, default a random port between [49152, 65536]')
    gp2.add_argument('--host_in', type=str, default=__default_host__,
                     help='host address for input, by default it is %s' % __default_host__)
    gp2.add_argument('--host_out', type=str, default=__default_host__,
                     help='host address for output, by default it is %s' % __default_host__)
    gp2.add_argument('--socket_in', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PULL_BIND,
                     help='socket type for input port')
    gp2.add_argument('--socket_out', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PUSH_BIND,
                     help='socket type for output port')
    gp2.add_argument('--port_ctrl', type=int, default=os.environ.get('JINA_CONTROL_PORT', random_port()),
                     help='port for controlling the pod, default a random port between [49152, 65536]')
    gp2.add_argument('--ctrl_with_ipc', action='store_true', default=False,
                     help='use ipc protocol for control socket')
    gp2.add_argument('--timeout', type=int, default=-1,
                     help='timeout (ms) of all requests, -1 for waiting forever')
    gp2.add_argument('--timeout_ctrl', type=int, default=5000,
                     help='timeout (ms) of the control request, -1 for waiting forever')
    gp2.add_argument('--timeout_ready', type=int, default=5000,
                     help='timeout (ms) of a pea is ready for request, -1 for waiting forever')

    gp3 = add_arg_group(parser, 'pea IO arguments')
    gp3.add_argument('--dump_interval', type=int, default=240,
                     help='serialize the model in the pod every n seconds if model changes. '
                          '-1 means --read_only. ')
    gp3.add_argument('--exit_no_dump', action='store_true', default=False,
                     help='do not serialize the model when the pod exits')
    gp3.add_argument('--read_only', action='store_true', default=False,
                     help='do not allow the pod to modify the model, '
                          'dump_interval will be ignored')
    gp3.add_argument('--separated_workspace', action='store_true', default=False,
                     help='the data and config files are separated for each pea in this pod, '
                          'only effective when Pod\'s `replicas` > 1')
    gp3.add_argument('--replica_id', type=int, default=-1,
                     help='the id of the storage of this replica, only effective when `separated_workspace=True`')

    gp5 = add_arg_group(parser, 'pea messaging arguments')
    gp5.add_argument('--check_version', action='store_true', default=False,
                     help='comparing the jina and proto version of incoming message with local setup, '
                          'mismatch raise an exception')
    gp5.add_argument('--array_in_pb', action='store_true', default=False,
                     help='sending raw_bytes and numpy ndarray together within or separately from the protobuf message, '
                          'the latter often yields a better network efficiency')
    gp5.add_argument('--num_part', type=int, default=1,
                     help='wait until the number of parts of message are all received')

    gp6 = add_arg_group(parser, 'pea EXPERIMENTAL arguments')
    gp6.add_argument('--memory_hwm', type=int, default=-1,
                     help='memory high watermark of this pod in Gigabytes, pod will restart when this is reached. '
                          '-1 means no restriction')
    gp6.add_argument('--runtime', type=str, choices=['thread', 'process'], default='thread',
                     help='the parallel runtime of the pod')

    _set_grpc_parser(parser)
    return parser


def set_pod_parser(parser=None):
    from ..enums import ReplicaType
    if not parser:
        parser = set_base_parser()
    set_pea_parser(parser)

    gp4 = add_arg_group(parser, 'pod replica arguments')
    gp4.add_argument('--replicas', type=int, default=1,
                     help='number of parallel peas in the pod running at the same time (i.e. replicas), '
                          '`port_in` and `port_out` will be set to random, '
                          'and routers will be added automatically when necessary')
    gp4.add_argument('--replica_type', type=ReplicaType.from_string, choices=list(ReplicaType),
                     default=ReplicaType.PUSH_NONBLOCK,
                     help='replica type of the concurrent peas')
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
    parser.add_argument('--print_response', action='store_true', default=False,
                        help='print the response when received')
    return parser


def _set_grpc_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from ..helper import random_port
    from .. import __default_host__
    gp1 = add_arg_group(parser, 'grpc and remote arguments')
    gp1.add_argument('--host', type=str, default=__default_host__,
                     help='host address of the pea/frontend, by default it is %s.' % __default_host__)
    gp1.add_argument('--port_grpc',
                     type=int,
                     default=random_port(),
                     help='host port of the grpc frontend')
    gp1.add_argument('--max_message_size', type=int, default=-1,
                     help='maximum send and receive size for grpc server in bytes, -1 means unlimited')
    gp1.add_argument('--proxy', action='store_true', default=False,
                     help='respect the http_proxy and https_proxy environment variables. '
                          'otherwise, it will unset these proxy variables before start. '
                          'gRPC seems to prefer --no_proxy')
    return parser


# def set_grpc_service_parser(parser=None):
#     if not parser:
#         parser = set_base_parser()
#     set_pod_parser(parser)
#     _set_grpc_parser(parser)
#
#     parser.add_argument('--pb2_path',
#                         type=str,
#                         required=True,
#                         help='the path of the python file protocol buffer compiler')
#     parser.add_argument('--pb2_grpc_path',
#                         type=str,
#                         required=True,
#                         help='the path of the python file generated by the gRPC Python protocol compiler plugin')
#     parser.add_argument('--stub_name',
#                         type=str,
#                         required=True,
#                         help='the name of the gRPC Stub')
#     parser.add_argument('--api_name',
#                         type=str,
#                         required=True,
#                         help='the api name for calling the stub')
#     return parser


def set_frontend_parser(parser=None):
    from ..enums import SocketType
    if not parser:
        parser = set_base_parser()
    set_pea_parser(parser)

    gp1 = add_arg_group(parser, 'frontend arguments')
    gp1.set_defaults(name='frontend',
                     socket_in=SocketType.PULL_CONNECT,  # otherwise there can be only one client at a time
                     socket_out=SocketType.PUSH_CONNECT,
                     ctrl_with_ipc=True,  # otherwise ctrl port would be conflicted
                     read_only=True)
    gp1.add_argument('--sleep_ms', type=int, default=50,
                     help='the sleep interval (ms) to control the frontend sending speed. '
                          'Note, sleep_ms=0 may result in bad load-balancing as all workload are pushed to one worker')
    gp1.add_argument('--allow_spawn', action='store_true', default=False,
                     help='accept the spawn requests sent from other remote Jina')
    return parser


def set_client_cli_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    _set_grpc_parser(parser)

    gp1 = add_arg_group(parser, 'client-specific arguments')
    _gp = gp1.add_mutually_exclusive_group()

    gp1.add_argument('--batch_size', type=int, default=100,
                     help='the size of the request to split')
    gp1.add_argument('--mode', choices=['index', 'search', 'train'], type=str,
                     required=True,
                     help='the mode of the client and the server')
    gp1.add_argument('--top_k', type=int,
                     default=10,
                     help='top_k results returned in the search mode')
    gp1.add_argument('--first_doc_id', type=int,
                     default=0,
                     help='the starting number of doc id, the consequent doc_id will increment by one')
    gp1.add_argument('--in_proto', action='store_true', default=False,
                     help='if the input data is already in protobuf Document format, or in raw bytes')
    _gp.add_argument('--first_request_id', type=int,
                     default=0,
                     help='the starting number of request id, the consequent request_id will increment by one')
    _gp.add_argument('--random_doc_id', action='store_true', default=False,
                     help='randomize the doc_id, if this is set then `first_request_id` is ignored')
    gp1.add_argument('--timeout_ready', type=int, default=5000,
                     help='timeout (ms) of a pea is ready for request, -1 for waiting forever')
    return parser


def get_main_parser():
    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(dest='cli',
                               description='use "%(prog)-8s [sub-command] --help" '
                                           'to get detailed information about each sub-command', required=True)

    # cli
    set_pod_parser(sp.add_parser('pod', help='start a pod', formatter_class=_chf))
    set_pea_parser(sp.add_parser('pea', help='start a pea', formatter_class=_chf))
    set_frontend_parser(sp.add_parser('frontend', help='start a frontend pod', formatter_class=_chf))
    set_client_cli_parser(
        sp.add_parser('client', help='start a client and connect it to a frontend', formatter_class=_chf))
    set_flow_parser(sp.add_parser('flow', help='start a flow from a YAML file', formatter_class=_chf))
    # set_grpc_service_parser(sp.add_parser('grpc', help='start a general purpose grpc service', formatter_class=adf))

    # # check
    # pp = sp.add_parser('check', help='check jina config, settings, imports, network etc', formatter_class=_chf)
    # spp = pp.add_subparsers(dest='check',
    #                         description='use "%(prog)-8s check [sub-command] --help" '
    #                                     'to get detailed information about each sub-command', required=True)

    set_ping_parser(
        sp.add_parser('ping', help='ping a pod for a network health check', formatter_class=_chf))
    sp.add_parser('check', help='check the import status all executors and drivers', formatter_class=_chf)
    set_logger_parser(sp.add_parser('log', help='receive piped log output and beautify the log', formatter_class=_chf))
    return parser


class _ColoredHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):

    def start_section(self, heading):
        self._indent()
        section = self._Section(self, self._current_section, colored(heading, attrs=['bold', 'underline']))
        self._add_item(section.format_help, [])
        self._current_section = section

    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if isinstance(action, argparse._StoreTrueAction):

                    help += colored(' (default: %s)' % (
                        'enabled' if action.default else 'disabled, use "--%s" to enable it' % action.dest),
                                    attrs=['dark'])
                elif action.choices:
                    choices_str = '{%s}' % ', '.join([str(c) for c in action.choices])
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
                result = '{%s ... %d more choices}' % (choice_strs, len(action.choices) - 4)
            else:
                choice_strs = ', '.join([str(c) for c in action.choices])
                result = '{%s}' % choice_strs
        else:
            result = default_metavar

        def format(tuple_size):
            if isinstance(result, tuple):
                return result
            else:
                return (result,) * tuple_size

        return format


_chf = _ColoredHelpFormatter
