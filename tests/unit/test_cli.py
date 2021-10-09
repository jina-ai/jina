import json
import os
import subprocess

import pytest

from cli.autocomplete import ac_table
from cli.export import api_to_dict
from cli.lookup import _build_lookup_table, lookup_and_print
from jina.checker import NetworkChecker
from jina.jaml import JAML
from jina.parsers import set_pod_parser, set_pea_parser
from jina.parsers.ping import set_ping_parser
from jina.peapods import Pea


def test_export_api(tmpdir):
    with open(tmpdir / 'test.yml', 'w', encoding='utf8') as fp:
        JAML.dump(api_to_dict(), fp)
    with open(tmpdir / 'test.json', 'w', encoding='utf8') as fp:
        json.dump(api_to_dict(), fp)


@pytest.mark.parametrize('cli', ac_table['commands'])
def test_help_lookup(cli, capsys):
    nkw2kw, kw2info = _build_lookup_table()
    if cli not in {'--help', '--version', '--version-full'}:
        assert cli in nkw2kw
        lookup_and_print(cli)
        captured = capsys.readouterr()
        assert captured.out


def test_main_cli():
    subprocess.check_call(['jina'])


def test_cli_help():
    subprocess.check_call(['jina', 'help', 'pod'])


def test_cli_warn_unknown_args():
    subprocess.check_call(['jina', 'help', 'pod', '--abcdefg'])


@pytest.mark.parametrize('cli', ac_table['commands'])
def test_all_cli(cli):
    subprocess.check_call(['jina', cli, '--help'])


@pytest.mark.parametrize('smethod', ['fork', 'spawn'])
def test_all_start_method(smethod):
    s = subprocess.check_output(
        ['jina', '-v'],
        env=dict(os.environ, JINA_MP_START_METHOD=smethod),
        stderr=subprocess.STDOUT,
    )
    assert 'UserWarning' in s.decode()
    assert smethod in s.decode()


def test_parse_env_map():
    a = set_pod_parser().parse_args(['--env', 'key1=value1', '--env', 'key2=value2'])
    assert a.env == {'key1': 'value1', 'key2': 'value2'}

    a = set_pod_parser().parse_args(['--env', 'key1=value1', 'key2=value2', 'key3=3'])
    assert a.env == {'key1': 'value1', 'key2': 'value2', 'key3': 3}


@pytest.mark.slow
def test_ping():
    a1 = set_pea_parser().parse_args([])
    a2 = set_ping_parser().parse_args(
        ['0.0.0.0', str(a1.port_ctrl), '--print-response']
    )

    a3 = set_ping_parser().parse_args(
        ['0.0.0.1', str(a1.port_ctrl), '--timeout', '1000']
    )

    with pytest.raises(SystemExit) as cm:
        with Pea(a1):
            NetworkChecker(a2)

    assert cm.value.code == 0

    # test with bad address
    with pytest.raises(SystemExit) as cm:
        with Pea(a1):
            NetworkChecker(a3)

    assert cm.value.code == 1


@pytest.mark.parametrize('project', ['fashion', 'chatbot', 'multimodal'])
def test_fork(tmpdir, project):
    subprocess.check_call(['jina', 'hello', 'fork', project, f'{tmpdir}/tmp'])

    assert os.path.exists(f'{tmpdir}/tmp/app.py')
    assert os.path.exists(f'{tmpdir}/tmp/my_executors.py')
    if project == 'multimodal':
        assert os.path.exists(f'{tmpdir}/tmp/flow-index.yml')
        assert os.path.exists(f'{tmpdir}/tmp/flow-search.yml')
