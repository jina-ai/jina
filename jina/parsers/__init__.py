def set_pea_parser(parser=None):
    """Set the parser for the Pea

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()

    from .peapods.base import mixin_base_ppr_parser
    from .peapods.runtimes.zmq import mixin_zmq_runtime_parser
    from .peapods.runtimes.zed import mixin_zed_runtime_parser
    from .peapods.runtimes.container import mixin_container_runtime_parser
    from .peapods.runtimes.remote import mixin_remote_parser
    from .peapods.pea import mixin_pea_parser
    from .peapods.runtimes.distributed import mixin_distributed_feature_parser

    mixin_base_ppr_parser(parser)
    mixin_zmq_runtime_parser(parser)
    mixin_zed_runtime_parser(parser)
    mixin_container_runtime_parser(parser)
    mixin_remote_parser(parser)
    mixin_distributed_feature_parser(parser)
    mixin_pea_parser(parser)

    return parser


def set_pod_parser(parser=None):
    """Set the parser for the Pod

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()

    set_pea_parser(parser)

    from .peapods.pod import mixin_base_pod_parser

    mixin_base_pod_parser(parser)

    return parser


def set_gateway_parser(parser=None):
    """Set the parser for the gateway arguments

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()

    from .peapods.base import mixin_base_ppr_parser
    from .peapods.runtimes.zmq import mixin_zmq_runtime_parser
    from .peapods.runtimes.zed import mixin_zed_runtime_parser
    from .peapods.runtimes.container import mixin_container_runtime_parser
    from .peapods.runtimes.remote import (
        mixin_remote_parser,
        mixin_grpc_server_parser,
        mixin_rest_server_parser,
    )
    from .peapods.pea import mixin_pea_parser

    mixin_base_ppr_parser(parser)
    mixin_zmq_runtime_parser(parser)
    mixin_zed_runtime_parser(parser)
    mixin_grpc_server_parser(parser)
    mixin_rest_server_parser(parser)
    mixin_remote_parser(parser)
    mixin_pea_parser(parser)

    from ..enums import SocketType, PodRoleType

    parser.set_defaults(
        name='gateway',
        socket_in=SocketType.PULL_CONNECT,  # otherwise there can be only one client at a time
        socket_out=SocketType.PUSH_CONNECT,
        ctrl_with_ipc=True,  # otherwise ctrl port would be conflicted
        runtime_cls='GRPCRuntime',
        pod_role=PodRoleType.GATEWAY,
    )

    parser.add_argument(
        '--restful',
        action='store_true',
        default=False,
        help='If set, use RESTful interface instead of gRPC as the main interface',
    )
    return parser


def set_client_cli_parser(parser=None):
    """Set the parser for the cli client

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()

    from .peapods.runtimes.remote import mixin_remote_parser
    from .client import mixin_client_features_parser, mixin_client_type_parser

    mixin_remote_parser(parser)
    mixin_client_type_parser(parser)
    mixin_client_features_parser(parser)

    return parser


def get_main_parser():
    """The main parser for Jina

    :return: the parser
    """
    from .base import set_base_parser
    from .helloworld import set_hw_parser, set_hello_parser
    from .helper import _chf, _SHOW_ALL_ARGS

    from .export_api import set_export_api_parser
    from .flow import set_flow_parser
    from .ping import set_ping_parser

    # from .hub import set_hub_parser
    # from .optimizer import set_optimizer_parser

    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(
        dest='cli',
        description='''
        Use `%(prog)-8s [sub-command] --help` to get detailed information about each sub-command. 
        
        To show all commands, run `JINA_FULL_CLI=1 jina --help`.
        ''',
        required=True,
    )

    set_hello_parser(
        sp.add_parser(
            'hello',
            help='👋 Hello Jina!',
            description='Start hello world demos.',
            formatter_class=_chf,
        )
    )

    set_pod_parser(
        sp.add_parser(
            'executor',
            aliases=['pod'],
            help='Start an Executor',
            description='Start an Executor. Executor is how Jina processes Document.',
            formatter_class=_chf,
        )
    )

    set_flow_parser(
        sp.add_parser(
            'flow',
            description='Start a Flow. Flow is how Jina streamlines and distributes Executors.',
            help='Start a Flow',
            formatter_class=_chf,
        )
    )

    set_ping_parser(
        sp.add_parser(
            'ping',
            help='Ping an Executor',
            description='Ping a Pod and check its network connectivity.',
            formatter_class=_chf,
        )
    )

    set_gateway_parser(
        sp.add_parser(
            'gateway',
            description='Start a Gateway that receives client Requests via gRPC/REST interface',
            **(dict(help='Start a Gateway')) if _SHOW_ALL_ARGS else {},
            formatter_class=_chf,
        )
    )

    # set_hub_parser(
    #     sp.add_parser(
    #         'hub',
    #         help='Build, push, pull Jina Hub images',
    #         description='Build, push, pull Jina Hub images',
    #         formatter_class=_chf,
    #     )
    # )

    # Below are low-level / internal / experimental CLIs, hidden from users by default

    set_pea_parser(
        sp.add_parser(
            'pea',
            description='Start a Pea. '
            'You should rarely use this directly unless you '
            'are doing low-level orchestration',
            formatter_class=_chf,
            **(dict(help='Start a Pea')) if _SHOW_ALL_ARGS else {},
        )
    )

    set_client_cli_parser(
        sp.add_parser(
            'client',
            description='Start a Python client that connects to a remote Jina gateway',
            formatter_class=_chf,
            **(dict(help='Start a Client')) if _SHOW_ALL_ARGS else {},
        )
    )

    set_export_api_parser(
        sp.add_parser(
            'export-api',
            description='Export Jina API to JSON/YAML file for 3rd party applications',
            formatter_class=_chf,
            **(dict(help='Export Jina API to file')) if _SHOW_ALL_ARGS else {},
        )
    )

    return parser
