import subprocess

import pytest

from jina.parsers import set_pod_parser


@pytest.mark.parametrize('cli', ['pod', 'pea', 'gateway', 'log',
                                 'check', 'ping', 'client', 'flow', 'hello-world', 'export-api'])
def test_cli(cli):
    subprocess.check_call(['jina', cli, '--help'])


def test_main_cli():
    subprocess.check_call(['jina'])


def test_parse_env_map():
    a = set_pod_parser().parse_args(['--env', 'key1=value1',
                                     '--env', 'key2=value2'])
    assert a.env == {'key1': 'value1', 'key2': 'value2'}

    a = set_pod_parser().parse_args(['--env', 'key1=value1', 'key2=value2'])
    assert a.env == {'key1': 'value1', 'key2': 'value2'}
