import os
from distutils.dir_util import copy_tree
from shutil import copy2

from jina.optimizers.discovery import run_parameter_discovery

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_discovery(tmpdir):
    copy2(os.path.join(cur_dir, 'flow.yml'), tmpdir)
    pod_dir = os.path.join(tmpdir, 'pods')
    copy_tree(os.path.join(cur_dir, 'pods'), pod_dir)
    parameter_result_file = os.path.join(tmpdir, 'parameter.yml')
    run_parameter_discovery(
        [os.path.join(tmpdir, 'flow.yml')], parameter_result_file, True
    )
    assert os.path.exists(parameter_result_file)
