from jina.parsers.client import mixin_comm_protocol_parser
from jina.parsers.helper import _SHOW_ALL_ARGS
from jina.parsers.orchestrate.runtimes.head import mixin_head_parser


def set_pod_parser(parser=None, port_monitoring=True):
    """Set the parser for the Pod

    :param parser: an optional existing parser to build upon
    :param port_monitoring: if to include the port parsing
    :return: the parser
    """
    if not parser:
        from jina.parsers.base import set_base_parser

        parser = set_base_parser()

    from jina.parsers.hubble.pull import mixin_hub_pull_options_parser
    from jina.parsers.orchestrate.base import mixin_base_ppr_parser
    from jina.parsers.orchestrate.pod import mixin_pod_parser
    from jina.parsers.orchestrate.runtimes.container import (
        mixin_container_runtime_parser,
    )
    from jina.parsers.orchestrate.runtimes.distributed import (
        mixin_distributed_feature_parser,
    )
    from jina.parsers.orchestrate.runtimes.remote import mixin_remote_runtime_parser
    from jina.parsers.orchestrate.runtimes.worker import mixin_worker_runtime_parser

    mixin_base_ppr_parser(parser)
    mixin_worker_runtime_parser(parser)
    mixin_container_runtime_parser(parser)
    mixin_remote_runtime_parser(parser)
    mixin_distributed_feature_parser(parser)
    mixin_pod_parser(parser, port_monitoring=port_monitoring)
    mixin_hub_pull_options_parser(parser)
    mixin_head_parser(parser)

    return parser


def set_deployment_parser(parser=None):
    """Set the parser for the Deployment

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        from jina.parsers.base import set_base_parser

        parser = set_base_parser()

    set_pod_parser(parser, port_monitoring=False)

    from jina.parsers.orchestrate.deployment import mixin_base_deployment_parser

    mixin_base_deployment_parser(parser)

    return parser


def set_gateway_parser(parser=None):
    """Set the parser for the gateway arguments

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        from jina.parsers.base import set_base_parser

        parser = set_base_parser()

    from jina.parsers.orchestrate.base import mixin_base_ppr_parser
    from jina.parsers.orchestrate.pod import mixin_pod_parser
    from jina.parsers.orchestrate.runtimes.remote import (
        mixin_gateway_parser,
        mixin_graphql_parser,
        mixin_http_gateway_parser,
        mixin_prefetch_parser,
    )
    from jina.parsers.orchestrate.runtimes.worker import mixin_worker_runtime_parser

    mixin_base_ppr_parser(parser)
    mixin_worker_runtime_parser(parser)
    mixin_prefetch_parser(parser)
    mixin_http_gateway_parser(parser)
    mixin_graphql_parser(parser)
    mixin_comm_protocol_parser(parser)
    mixin_gateway_parser(parser)
    mixin_pod_parser(parser)

    from jina.enums import DeploymentRoleType

    parser.set_defaults(
        name='gateway',
        runtime_cls='GRPCGatewayRuntime',
        deployment_role=DeploymentRoleType.GATEWAY,
    )

    return parser


def set_client_cli_parser(parser=None):
    """Set the parser for the cli client

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        from jina.parsers.base import set_base_parser

        parser = set_base_parser()

    from jina.parsers.client import (
        mixin_client_features_parser,
        mixin_comm_protocol_parser,
    )
    from jina.parsers.orchestrate.runtimes.remote import mixin_client_gateway_parser

    mixin_client_gateway_parser(parser)
    mixin_client_features_parser(parser)
    mixin_comm_protocol_parser(parser)

    return parser


def set_help_parser(parser=None):
    """Set the parser for the jina help lookup

    :param parser: an optional existing parser to build upon
    :return: the parser
    """

    if not parser:
        from jina.parsers.base import set_base_parser

        parser = set_base_parser()

    parser.add_argument(
        'query',
        type=str,
        help='Lookup the usage & mention of the argument name in Jina API. The name can be fuzzy',
    )
    return parser


def get_main_parser():
    """The main parser for Jina

    :return: the parser
    """
    from jina.parsers.base import set_base_parser
    from jina.parsers.create import set_new_project_parser
    from jina.parsers.export import set_export_parser
    from jina.parsers.flow import set_flow_parser
    from jina.parsers.helper import _SHOW_ALL_ARGS, _chf
    from jina.parsers.hubble import set_hub_parser
    from jina.parsers.ping import set_ping_parser

    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(
        dest='cli',
        required=True,
    )

    set_pod_parser(
        sp.add_parser(
            'executor',
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
            description='Ping a Deployment and check its network connectivity.',
            formatter_class=_chf,
        )
    )

    set_export_parser(
        sp.add_parser(
            'export',
            help='Export Jina API/Flow',
            description='Export Jina API and Flow to JSONSchema, Kubernetes YAML, or SVG flowchart.',
            formatter_class=_chf,
        )
    )

    set_new_project_parser(
        sp.add_parser(
            'new',
            help='Create a new Jina project',
            description='Create a new Jina toy project with the predefined template.',
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

    set_hub_parser(
        sp.add_parser(
            'hub',
            help='Push/pull an Executor to/from Jina Hub',
            description='Push/Pull an Executor to/from Jina Hub',
            formatter_class=_chf,
        )
    )

    set_help_parser(
        sp.add_parser(
            'help',
            help='Show help text of a CLI argument',
            description='Show help text of a CLI argument',
            formatter_class=_chf,
        )
    )
    # Below are low-level / internal / experimental CLIs, hidden from users by default

    set_pod_parser(
        sp.add_parser(
            'pod',
            description='Start a Pod. '
            'You should rarely use this directly unless you '
            'are doing low-level orchestration',
            formatter_class=_chf,
            **(dict(help='Start a Pod')) if _SHOW_ALL_ARGS else {},
        )
    )

    set_deployment_parser(
        sp.add_parser(
            'deployment',
            description='Start a Deployment. '
            'You should rarely use this directly unless you '
            'are doing low-level orchestration',
            formatter_class=_chf,
            **(dict(help='Start a Deployment')) if _SHOW_ALL_ARGS else {},
        )
    )

    set_client_cli_parser(
        sp.add_parser(
            'client',
            description='Start a Python client that connects to a Jina gateway',
            formatter_class=_chf,
            **(dict(help='Start a Client')) if _SHOW_ALL_ARGS else {},
        )
    )

    return parser
