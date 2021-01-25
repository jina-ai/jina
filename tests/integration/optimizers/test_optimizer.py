import json
import os

import pytest
import yaml
from google.protobuf.json_format import MessageToJson

from jina import Document
from jina.jaml import JAML
from jina.optimizers import FlowOptimizer, MeanEvaluationCallback
from jina.optimizers import run_optimizer_cli
from jina.optimizers.flow_runner import SingleFlowRunner
from jina.parsers.optimizer import set_optimizer_parser

BEST_PARAMETERS = {
    'JINA_DUMMYCRAFTER_PARAM1': 0,
    'JINA_DUMMYCRAFTER_PARAM2': 1,
    'JINA_DUMMYCRAFTER_PARAM3': 1,
}


@pytest.fixture
def config(tmpdir):
    root = os.path.join('tests', 'integration', 'optimizers')
    os.environ['JINA_OPTIMIZER_FLOW_JAML_PATH'] = os.path.join(root, 'flow.yml')
    os.environ['JINA_OPTIMIZER_DATA_PATH'] = os.path.join(root, 'data.jsonlines')
    os.environ['JINA_OPTIMIZER_PARAMETER_PATH'] = os.path.join(root, 'parameter.yml')
    os.environ['JINA_OPTIMIZER_WORKSPACE_DIR'] = str(tmpdir)
    os.environ['JINA_OPTIMIZER_OUTPUT_FILE'] = os.path.join(tmpdir, 'best_parameters.yml')
    yield
    del os.environ['JINA_OPTIMIZER_FLOW_JAML_PATH']
    del os.environ['JINA_OPTIMIZER_DATA_PATH']
    del os.environ['JINA_OPTIMIZER_PARAMETER_PATH']
    del os.environ['JINA_OPTIMIZER_WORKSPACE_DIR']
    del os.environ['JINA_OPTIMIZER_OUTPUT_FILE']


def document_generator(num_doc):
    for _ in range(num_doc):
        doc = Document(content='hello')
        groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc


@pytest.mark.parametrize('use_output_file', (True, False))
def test_optimizer(tmpdir, use_output_file):
    eval_flow_runner = SingleFlowRunner(
        flow_yaml=os.path.join('tests', 'integration', 'optimizers', 'flow.yml'),
        documents=document_generator(10),
        request_size=1,
        task='search',
    )
    output_file = os.path.join(tmpdir, 'results', 'best_parameters.yml')
    output_file_param = output_file if use_output_file else None
    opt = FlowOptimizer(
        flow_runner=eval_flow_runner,
        parameter_yaml=os.path.join('tests', 'integration', 'optimizers', 'parameter.yml'),
        evaluation_callback=MeanEvaluationCallback(),
        workspace_base_dir=str(tmpdir),
        output_file=output_file_param,
        n_trials=5,
    )
    result = opt.optimize_flow()
    assert result.best_parameters == BEST_PARAMETERS
    validate_results(output_file, use_output_file)


def validate_results(output_file, use_output_file):
    if use_output_file:
        assert yaml.load(open(output_file)) == BEST_PARAMETERS
    else:
        with pytest.raises(FileNotFoundError):
            _ = open(output_file)


@pytest.mark.parametrize('use_output_file', (True, False))
def test_yaml(tmpdir, use_output_file):
    jsonlines_file = os.path.join(tmpdir, 'docs.jsonlines')
    output_file = os.path.join(tmpdir, 'results', 'best_parameters.yml')
    optimizer_yaml = f'''!FlowOptimizer
version: 1
with:
  flow_runner: !SingleFlowRunner
    with:
      flow_yaml: {os.path.join('tests', 'integration', 'optimizers', 'flow.yml')}
      documents: {jsonlines_file}
      request_size: 1
      task: 'search_lines'
  evaluation_callback: !MeanEvaluationCallback {{}}
  parameter_yaml: {os.path.join('tests', 'integration', 'optimizers', 'parameter.yml')}
  workspace_base_dir: {tmpdir}
  {f"output_file: {output_file}" if use_output_file else ''}
  n_trials: 5
'''
    documents = document_generator(10)
    with open(jsonlines_file, 'w') as f:
        for document, groundtruth_doc in documents:
            document.id = ""
            groundtruth_doc.id = ""
            json.dump(
                {
                    'document': json.loads(MessageToJson(document).replace('\n', '')),
                    'groundtruth': json.loads(MessageToJson(groundtruth_doc).replace('\n', '')),
                },
                f,
            )
            f.write('\n')

    optimizer = JAML.load(optimizer_yaml)
    result = optimizer.optimize_flow()
    assert result.best_parameters == BEST_PARAMETERS
    validate_results(output_file, use_output_file)


def test_cli(config):
    run_optimizer_cli(
        set_optimizer_parser().parse_args(
            [
                '--uses',
                os.path.join('tests', 'integration', 'optimizers', 'optimizer_conf.yml')
            ]
        )
    )
    validate_results(os.environ['JINA_OPTIMIZER_OUTPUT_FILE'], True)
