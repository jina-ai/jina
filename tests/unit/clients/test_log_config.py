import os

from jina import Deployment, Flow

cur_dir = os.path.abspath(os.path.dirname(__file__))


def test_log_config_arg():
    log_config_file = 'logging.custom.yml'
    cli_args = ['--log-config', log_config_file]

    from jina.parsers import set_client_cli_parser

    args = set_client_cli_parser().parse_args(cli_args)
    assert args.log_config == log_config_file


def test_log_config_flow():
    log_config_file = os.path.join(cur_dir, '../logging/yaml/file.yml')
    flow = Flow(log_config=log_config_file)
    client = flow.client
    assert client.args.log_config == log_config_file


def test_log_config_deployment():
    log_config_file = os.path.join(cur_dir, '../logging/yaml/file.yml')
    deployment = Deployment(log_config=log_config_file)
    client = deployment.client
    assert client.args.log_config == log_config_file
