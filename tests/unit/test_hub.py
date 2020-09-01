import os

import pytest
from jina.docker.hubio import HubIO
from jina.main.parser import set_hub_build_parser, set_hub_pushpull_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.timeout(360)
def test_hub_build_pull():
    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--pull', '--push'])
    HubIO(args).build()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder'])
    HubIO(args).pull()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder:0.0.6'])
    HubIO(args).pull()


def test_hub_build_failures():
    for j in ['bad-dockerfile', 'bad-pythonfile', 'missing-dockerfile', 'missing-manifest']:
        args = set_hub_build_parser().parse_args(
            [os.path.join(cur_dir, 'hub-mwu-bad', j), '--pull', '--push'])
        assert HubIO(args).build()['is_build_success'] == False
