import json
import os

import pytest
import yaml
from google.protobuf.json_format import MessageToJson

from jina import Document
from jina.jaml import JAML
from jina.optimizers import FlowOptimizer, MeanEvaluationCallback
from jina.optimizers import run_optimizer_cli
from jina.optimizers.flow_runner import SingleFlowRunner, MultiFlowRunner
from jina.parsers.optimizer import set_optimizer_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))

BEST_PARAMETERS = {
    'JINA_DUMMYCRAFTER_PARAM1': 0,
    'JINA_DUMMYCRAFTER_PARAM2': 1,
    'JINA_DUMMYCRAFTER_PARAM3': 1,
}


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_OPTIMIZER_WORKSPACE_DIR'] = str(tmpdir)
    os.environ['JINA_OPTIMIZER_PARAMETER_FILE'] = os.path.join(cur_dir, 'parameter.yml')
    os.environ['JINA_OPTIMIZER_DATA_FILE'] = os.path.join(cur_dir, 'data.jsonlines')
    yield
    del os.environ['JINA_OPTIMIZER_WORKSPACE_DIR']
    del os.environ['JINA_OPTIMIZER_PARAMETER_FILE']
    del os.environ['JINA_OPTIMIZER_DATA_FILE']


def validate_result(result, tmpdir):
    result_path = os.path.join(tmpdir, 'out/best_parameters.yml')
    result.save_parameters(result_path)
    print(f' result_bestparams {result.best_parameters}')
    assert result.best_parameters == BEST_PARAMETERS
    assert yaml.load(open(result_path)) == BEST_PARAMETERS


def document_generator(num_doc):
    for _ in range(num_doc):
        doc = Document(content='hello')
        groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc


def test_optimizer_single_flow(tmpdir, config):
    eval_flow_runner = SingleFlowRunner(
        flow_yaml=os.path.join(cur_dir, 'flow_pod_choice.yml'),
        documents=document_generator(10),
        request_size=1,
        execution_endpoint='search',
    )
    opt = FlowOptimizer(
        flow_runner=eval_flow_runner,
        parameter_yaml=os.path.join(cur_dir, 'parameter_pod_choice.yml'),
        evaluation_callback=MeanEvaluationCallback(),
        workspace_base_dir=str(tmpdir),
        n_trials=5,
    )
    result = opt.optimize_flow()
    validate_result(result, tmpdir)
