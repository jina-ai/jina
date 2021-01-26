import os
from shutil import copy2
from distutils.dir_util import copy_tree

import pytest

from jina.optimizers.discovery import run_parameter_discovery

@pytest.fixture
def config(tmpdir):
    os.environ['JINA_OPTIMIZER_CRAFTER_FILE'] = os.path.join('pods', 'craft.yml')
    os.environ['JINA_OPTIMIZER_EVALUATOR_FILE'] = os.path.join('pods', 'evaluate.yml')
    yield
    del os.environ['JINA_OPTIMIZER_CRAFTER_FILE']
    del os.environ['JINA_OPTIMIZER_EVALUATOR_FILE']

# TODO needs refactoring
@pytest.mark.skip(reason="the implementation does not work with environment variables")
def test_discovery(tmpdir, config):
    copy2(os.path.join('tests', 'integration', 'optimizers', 'flow.yml'), tmpdir)
    pod_dir = os.path.join(tmpdir, 'pods')
    copy_tree(os.path.join('tests', 'integration', 'optimizers', 'pods'), pod_dir)
    parameter_result_file = os.path.join(tmpdir, 'parameter.yml')
    run_parameter_discovery([os.path.join(tmpdir, 'flow.yml')], parameter_result_file, True)
    assert os.path.exists(parameter_result_file)

