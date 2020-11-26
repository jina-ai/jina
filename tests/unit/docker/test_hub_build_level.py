import os

import pytest

from pathlib import Path
from jina.docker.hubio import HubIO
from jina.helper import yaml
from jina.enums import BuildTestLevel
from jina.peapods import Pod
from jina.executors import BaseExecutor
from jina.parser import set_hub_build_parser

cur_dir = Path.cwd()

def test_hub_build_pull():
    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--push', '--host-info', '--test-level', 'FLOW'])
    p_names, failed_levels = HubIO(args)._test_build("jinahub/pod.dummy_mwu_encoder")

    expected_failed_levels = [BuildTestLevel.EXECUTOR, BuildTestLevel.POD_NONDOCKER, BuildTestLevel.FLOW]
    assert expected_failed_levels == failed_levels

    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--push', '--host-info', '--test-level', 'EXECUTOR'])
    p_names, failed_levels = HubIO(args)._test_build("jinahub/pod.dummy_mwu_encoder")

    expected_failed_levels = [BuildTestLevel.EXECUTOR]
    assert expected_failed_levels == failed_levels

    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--push', '--host-info', '--test-level', 'POD_DOCKER'])
    p_names, failed_levels = HubIO(args)._test_build("jinahub/pod.dummy_mwu_encoder")

    expected_failed_levels = [BuildTestLevel.EXECUTOR, BuildTestLevel.POD_NONDOCKER]
    assert expected_failed_levels == failed_levels

    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--push', '--host-info', '--test-level', 'POD_NONDOCKER'])
    p_names, failed_levels = HubIO(args)._test_build("jinahub/pod.dummy_mwu_encoder")

    expected_failed_levels = [BuildTestLevel.EXECUTOR, BuildTestLevel.POD_NONDOCKER]
    assert expected_failed_levels == failed_levels
