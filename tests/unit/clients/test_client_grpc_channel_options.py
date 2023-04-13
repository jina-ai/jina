import pytest

from jina import Deployment, Flow


@pytest.mark.parametrize('options', ['{"grpc.keepalive_time_ms": 9999}', None])
def test_grpc_channel_options(options):
    cli_args = []
    if options:
        cli_args = ['--grpc-channel-options', options]

    from jina.parsers import set_client_cli_parser

    args = set_client_cli_parser().parse_args(cli_args)
    args.grpc_channel_options = options


def test_grpc_channel_options_config_gateway():
    options = {"grpc.keepalive_time_ms": 9999}
    flow = Flow().config_gateway(grpc_channel_options=options)
    client = flow.client
    assert client.args.grpc_channel_options == options


def test_grpc_channel_options_deployment():
    options = {"grpc.keepalive_time_ms": 9999}
    deployment = Deployment(grpc_channel_options=options)
    client = deployment.client
    assert client.args.grpc_channel_options == options
