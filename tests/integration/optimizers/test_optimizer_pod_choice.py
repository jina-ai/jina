import os

import pytest

from jina import Document
from jina.optimizers import FlowOptimizer, EvaluationCallback
from jina.optimizers.flow_runner import SingleFlowRunner

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_OPTIMIZER_WORKSPACE_DIR'] = str(tmpdir)
    os.environ['JINA_OPTIMIZER_PARAMETER_FILE'] = os.path.join(cur_dir, 'parameter.yml')
    os.environ['JINA_OPTIMIZER_DATA_FILE'] = os.path.join(cur_dir, 'data.jsonlines')
    yield
    del os.environ['JINA_OPTIMIZER_WORKSPACE_DIR']
    del os.environ['JINA_OPTIMIZER_PARAMETER_FILE']
    del os.environ['JINA_OPTIMIZER_DATA_FILE']


def document_generator_option1(num_doc):
    for _ in range(num_doc):
        doc = Document(content='DummyCrafterOption1')
        groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc


def document_generator_option2(num_doc):
    for _ in range(num_doc):
        doc = Document(content='DummyCrafterOption2')
        groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc


def test_optimizer_single_flow_option1(tmpdir, config):
    eval_flow_runner = SingleFlowRunner(
        flow_yaml=os.path.join(cur_dir, 'flow_pod_choice.yml'),
        documents=document_generator_option1(10),
        request_size=1,
        execution_endpoint='search',
    )
    opt = FlowOptimizer(
        flow_runner=eval_flow_runner,
        parameter_yaml=os.path.join(cur_dir, 'parameter_pod_choice.yml'),
        evaluation_callback=EvaluationCallback(),
        workspace_base_dir=str(tmpdir),
        n_trials=10,
    )
    result = opt.optimize_flow()
    assert (
        result.best_parameters['JINA_DUMMYCRAFTER_CHOICE'] == 'pods/craft_option1.yml'
    )
    assert result.best_parameters['JINA_DUMMYCRAFTER_PARAM1'] == 0
    assert result.best_parameters['JINA_DUMMYCRAFTER_PARAM2'] == 1
    assert result.best_parameters['JINA_DUMMYCRAFTER_PARAM3'] == 1


def test_optimizer_single_flow_option2(tmpdir, config):
    eval_flow_runner = SingleFlowRunner(
        flow_yaml=os.path.join(cur_dir, 'flow_pod_choice.yml'),
        documents=document_generator_option2(10),
        request_size=1,
        execution_endpoint='search',
    )
    opt = FlowOptimizer(
        flow_runner=eval_flow_runner,
        parameter_yaml=os.path.join(cur_dir, 'parameter_pod_choice.yml'),
        evaluation_callback=EvaluationCallback(),
        workspace_base_dir=str(tmpdir),
        n_trials=20,
    )
    result = opt.optimize_flow()
    assert (
        result.best_parameters['JINA_DUMMYCRAFTER_CHOICE'] == 'pods/craft_option2.yml'
    )
    assert result.best_parameters['JINA_DUMMYCRAFTER_PARAM4'] == 0
    assert result.best_parameters['JINA_DUMMYCRAFTER_PARAM5'] == 1
    assert result.best_parameters['JINA_DUMMYCRAFTER_PARAM6'] == 1
