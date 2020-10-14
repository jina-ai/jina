import subprocess

import pytest


@pytest.mark.parametrize('cli', ['pod', 'pea', 'gateway', 'log',
                                 'check', 'ping', 'client', 'flow', 'hello-world', 'export-api'])
def test_cli(cli):
    subprocess.check_call(['jina', cli, '--help'])


def test_main_cli():
    subprocess.check_call(['jina'])
