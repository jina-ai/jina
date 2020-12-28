from pathlib import Path

import pytest
import os

from jina.docker.hubio import HubIO
from jina.docker import hubapi
from jina.excepts import ImageAlreadyExists
from jina.jaml import JAML
from jina.helper import expand_dict
from jina.docker.helper import credentials_file
from jina.parser import set_hub_build_parser, set_hub_list_parser, set_hub_pushpull_parser

cur_dir = Path(__file__).parent

@pytest.mark.timeout(360)
def test_hub_build_pull():
    args = set_hub_build_parser().parse_args(
        [str(cur_dir / 'hub-mwu'), '--push', '--test-uses', '--raise-error'])
    HubIO(args).build()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder'])
    HubIO(args).pull()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder:0.0.6'])
    HubIO(args).pull()


@pytest.mark.timeout(360)
def test_hub_build_uses():
    args = set_hub_build_parser().parse_args(
        [str(cur_dir / 'hub-mwu'), '--test-uses', '--raise-error'])
    HubIO(args).build()
    # build again it shall not fail
    HubIO(args).build()

    args = set_hub_build_parser().parse_args(
        [str(cur_dir / 'hub-mwu'), '--test-uses', '--daemon', '--raise-error'])
    HubIO(args).build()
    # build again it shall not fail
    HubIO(args).build()


def test_hub_build_failures():
    for j in ['bad-dockerfile', 'bad-pythonfile', 'missing-dockerfile', 'missing-manifest']:
        args = set_hub_build_parser().parse_args(
            [str(cur_dir / 'hub-mwu-bad' / j)])
        assert not HubIO(args).build()['is_build_success']


def test_hub_build_no_pymodules():
    args = set_hub_build_parser().parse_args(
        [str(cur_dir / 'hub-mwu-bad' / 'fail-to-start')])
    assert HubIO(args).build()['is_build_success']

    args = set_hub_build_parser().parse_args(
        [str(cur_dir / 'hub-mwu-bad' / 'fail-to-start'), '--test-uses'])
    assert not HubIO(args).build()['is_build_success']
