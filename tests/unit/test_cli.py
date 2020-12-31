import subprocess

import pytest

from cli.autocomplete import ac_table
from jina.checker import NetworkChecker
from jina.parsers import set_pod_parser, set_pea_parser
from jina.parsers.ping import set_ping_parser
from jina.peapods import Pea


def test_main_cli():
    subprocess.check_call(['jina'])


@pytest.mark.parametrize('cli', ac_table['commands'])
def test_all_cli(cli):
    subprocess.check_call(['jina', cli, '--help'])


def test_parse_env_map():
    a = set_pod_parser().parse_args(['--env', 'key1=value1',
                                     '--env', 'key2=value2'])
    assert a.env == {'key1': 'value1', 'key2': 'value2'}

    a = set_pod_parser().parse_args(['--env', 'key1=value1', 'key2=value2'])
    assert a.env == {'key1': 'value1', 'key2': 'value2'}


def test_ping():
    a1 = set_pea_parser().parse_args([])
    a2 = set_ping_parser().parse_args(['0.0.0.0', str(a1.port_ctrl), '--print-response'])

    a3 = set_ping_parser().parse_args(['0.0.0.1', str(a1.port_ctrl), '--timeout', '1000'])

    with pytest.raises(SystemExit) as cm:
        with Pea(a1):
            NetworkChecker(a2)

    assert cm.value.code == 0

    # test with bad address
    with pytest.raises(SystemExit) as cm:
        with Pea(a1):
            NetworkChecker(a3)

    assert cm.value.code == 1
