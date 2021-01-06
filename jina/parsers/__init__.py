__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


def set_pea_parser(parser=None):
    if not parser:
        from .base import set_base_parser
        parser = set_base_parser()

    from .peapods.base import mixin_base_ppr_parser
    from .peapods.runtimes.zmq import mixin_zmq_runtime_parser
    from .peapods.runtimes.zed import mixin_zed_runtime_parser
    from .peapods.runtimes.container import mixin_container_runtime_parser
    from .peapods.runtimes.remote import mixin_remote_parser
    from .peapods.pea import mixin_pea_parser

    mixin_base_ppr_parser(parser)
    mixin_zmq_runtime_parser(parser)
    mixin_zed_runtime_parser(parser)
    mixin_container_runtime_parser(parser)
    mixin_remote_parser(parser)
    mixin_pea_parser(parser)

    return parser


def set_pod_parser(parser=None):
    if not parser:
        from .base import set_base_parser
        parser = set_base_parser()

    set_pea_parser(parser)

    from .peapods.pods.base import mixin_base_pod_parser

    mixin_base_pod_parser(parser)

    return parser


def set_gateway_parser(parser=None):
    if not parser:
        from .base import set_base_parser
        parser = set_base_parser()

    from .peapods.base import mixin_base_ppr_parser
    from .peapods.runtimes.zmq import mixin_zmq_runtime_parser
    from .peapods.runtimes.zed import mixin_zed_runtime_parser
    from .peapods.runtimes.container import mixin_container_runtime_parser
    from .peapods.runtimes.remote import mixin_remote_parser
    from .peapods.runtimes.remote import mixin_grpc_parser
    from .peapods.pea import mixin_pea_parser

    mixin_base_ppr_parser(parser)
    mixin_zmq_runtime_parser(parser)
    mixin_zed_runtime_parser(parser)
    mixin_grpc_parser(parser)
    mixin_remote_parser(parser)
    mixin_pea_parser(parser)

    from ..enums import SocketType, PodRoleType

    parser.set_defaults(name='gateway',
                        socket_in=SocketType.PULL_CONNECT,  # otherwise there can be only one client at a time
                        socket_out=SocketType.PUSH_CONNECT,
                        ctrl_with_ipc=True,  # otherwise ctrl port would be conflicted
                        read_only=True,
                        runtime_cls='GRPCRuntime',
                        pod_role=PodRoleType.GATEWAY)
    return parser


def set_client_cli_parser(parser=None):
    if not parser:
        from .base import set_base_parser
        parser = set_base_parser()

    from .peapods.runtimes.remote import mixin_grpc_parser, mixin_remote_parser
    from .client import mixin_client_cli_parser

    mixin_client_cli_parser(parser)
    mixin_grpc_parser(parser)
    mixin_remote_parser(parser)

    return parser


def get_main_parser():
    from .base import set_base_parser
    from .helloworld import set_hw_parser
    from .helper import _chf, _SHOW_ALL_ARGS
    from .check import set_check_parser
    from .export_api import set_export_api_parser
    from .flow import set_flow_parser
    from .hub import set_hub_parser
    from .logger import set_logger_parser
    from .ping import set_ping_parser

    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(dest='cli',
                               description='use "%(prog)-8s [sub-command] --help" '
                                           'to get detailed information about each sub-command', required=True)

    set_hw_parser(sp.add_parser('hello-world',
                                help='👋 Hello World! Hello Jina!',
                                description='Start the hello-world demo, a simple end2end image index and search demo '
                                            'without any extra dependencies.',
                                formatter_class=_chf))

    set_pod_parser(sp.add_parser('pod',
                                 help='start a pod',
                                 description='Start a Jina pod',
                                 formatter_class=_chf))

    set_flow_parser(sp.add_parser('flow',
                                  description='Start a Jina flow that consists of multiple pods',
                                  help='start a flow from a YAML file', formatter_class=_chf))

    set_gateway_parser(sp.add_parser('gateway',
                                     description='Start a Jina gateway that receives client remote requests via gRPC',
                                     help='start a gateway', formatter_class=_chf))

    set_ping_parser(sp.add_parser('ping',
                                  help='ping a pod and check the network connectivity',
                                  description='Ping a remote pod and check the network connectivity',
                                  formatter_class=_chf))

    set_check_parser(sp.add_parser('check',
                                   help='check the import status of all executors and drivers',
                                   description='Check the import status of all executors and drivers',
                                   formatter_class=_chf))

    set_hub_parser(sp.add_parser('hub', help='build, push, pull Jina Hub images',
                                 description='Build, push, pull Jina Hub images',
                                 formatter_class=_chf))

    # Below are low-level / internal / experimental CLIs, hidden from users by default

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

    set_client_cli_parser(sp.add_parser('client',
                                        description='Start a Python client that connects to a remote Jina gateway',
                                        formatter_class=_chf,
                                        **(dict(help='start a client')) if _SHOW_ALL_ARGS else {}))

    set_export_api_parser(sp.add_parser('export-api',
                                        description='Export Jina API to JSON/YAML file for 3rd party applications',
                                        formatter_class=_chf,
                                        **(dict(help='export Jina API to file')) if _SHOW_ALL_ARGS else {}))
    return parser
