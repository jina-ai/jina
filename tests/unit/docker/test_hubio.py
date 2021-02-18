import os

import pytest

from jina.docker.hubio import HubIO
from jina.parsers.hub import set_hub_new_parser


@pytest.mark.parametrize('new_type', ['pod', 'app', 'template'])
def test_create_new(tmpdir, new_type):
    args = set_hub_new_parser().parse_args(
        ['--output-dir', str(tmpdir), '--type', new_type])
    HubIO(args).new(no_input=True)
    list_dir = os.listdir(str(tmpdir))
    assert len(list_dir) == 1
